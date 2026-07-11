"""
Trigger và theo dõi Airflow DAG run bằng Airflow CLI (qua docker exec).

Thay vì dùng REST API + CSRF auth phức tạp, script gọi trực tiếp
`airflow` CLI bên trong container qua `docker exec`.

Usage:
    python script/trigger_dag.py Ethereum                          # trigger + monitor
    python script/trigger_dag.py Ethereum --cancel-all
    python script/trigger_dag.py Ethereum --status
    python script/trigger_dag.py Ethereum --no-wait
"""

import argparse
import json
import re
import subprocess
import sys
import time


CONTAINER = "chainslake-onprem-node01-1"
AIRFLOW_USER = "hadoop"

# Env cần thiết để airflow CLI hoạt động (từ airflow.sh)
_AIRFLOW_ENV = (
    "export PATH=$PATH:/home/hadoop/.local/bin && "
    "export PYTHONPATH=/home/hadoop/.local/lib/python3.8/site-packages"
)


def run_airflow_cmd(args, timeout=30):
    """Chạy airflow CLI bên trong container, trả về stdout."""
    cmd = [
        "docker", "exec", "-u", AIRFLOW_USER, CONTAINER,
        "bash", "-c",
        f"{_AIRFLOW_ENV} && airflow {args} 2>/dev/null"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode


def run_host_cmd(cmd, timeout=30):
    """Chạy shell command trên host."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode


def list_dags():
    """Liệt kê tất cả DAGs."""
    out, rc = run_airflow_cmd("dags list --output json")
    if rc != 0:
        print(f"Error listing DAGs: {out}")
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return []


def list_runs(dag_id, state=None, limit=10):
    """Liệt kê DAG runs."""
    cmd = f"dags list-runs -d {dag_id} -o json"
    if state:
        cmd += f" --state {state}"
    out, rc = run_airflow_cmd(cmd, timeout=60)
    if rc != 0:
        print(f"Error listing runs: {out}")
        return []
    try:
        runs = json.loads(out)
        return runs[:limit]
    except json.JSONDecodeError:
        return []


def trigger_dag(dag_id):
    """Trigger một DAG run mới."""
    out, rc = run_airflow_cmd(f"dags trigger {dag_id} -o json", timeout=60)
    if rc != 0:
        print(f"Error triggering DAG: {out}")
        return None

    # JSON output có thể bị lẫn log lines, tìm array JSON trong output
    try:
        # Tìm start của JSON array
        idx = out.find("[{")
        if idx >= 0:
            data = json.loads(out[idx:])
            if data:
                return data[0]
    except json.JSONDecodeError:
        pass

    # Fallback: parse run_id từ output text
    match = re.search(r'"dag_run_id"\s*:\s*"([^"]+)"', out)
    if match:
        return {"dag_run_id": match.group(1)}

    print(f"Could not parse trigger output: {out}")
    return None


def get_task_states(dag_id, run_id):
    """Lấy trạng thái các tasks trong một DAG run."""
    cmd = f"tasks states-for-dag-run {dag_id} {run_id} -o json"
    out, rc = run_airflow_cmd(cmd, timeout=60)
    if rc != 0:
        # Thử parse text output nếu JSON fail
        return parse_task_states_text(out)
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return parse_task_states_text(out)


def parse_task_states_text(text):
    """Parse task states từ text output (không phải JSON)."""
    tasks = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("dag_id"):
            continue
        # Format: dag_id | run_id | task_id | state | ...
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4:
            tasks.append({
                "task_id": parts[2],
                "state": parts[3],
            })
    return tasks


def set_dag_paused(dag_id, paused):
    """Pause/unpause DAG."""
    action = "pause" if paused else "unpause"
    out, rc = run_airflow_cmd(f"dags {action} {dag_id}")
    return rc == 0


def cancel_all_runs(dag_id):
    """
    Pause DAG để ngăn run mới.

    Lưu ý: Airflow CLI không hỗ trợ trực tiếp cancel một DAG run.
    Strategy: pause DAG → report các runs đang chạy.
    """
    set_dag_paused(dag_id, True)
    runs = list_runs(dag_id, limit=20)
    active = [r for r in runs if r.get("state") in ("running", "queued")]

    if not active:
        print("  No running/queued runs found.")
        return 0

    print(f"  DAG paused. Found {len(active)} active run(s):")
    for r in active:
        print(f"    - {r.get('run_id', 'unknown')} ({r.get('state')})")

    return len(active)


def show_status(dag_id):
    """Hiển thị status các DAG runs gần nhất."""
    runs = list_runs(dag_id, limit=5)
    if not runs:
        print(f"No runs found for DAG '{dag_id}'")
        return

    for r in runs:
        run_id = r.get("run_id", "unknown")
        state = r.get("state", "unknown")
        print(f"\n{'='*60}")
        print(f"Run:  {run_id}")
        print(f"State: {state}")

        tasks = get_task_states(dag_id, run_id)
        for t in tasks:
            tid = t.get("task_id", "?")
            ts = t.get("state", "?")
            icon = {"success": "OK", "failed": "XX", "running": "..", "queued": ".."}.get(ts, "--")
            print(f"  [{icon}] {tid}: {ts}")


def trigger_and_monitor(dag_id, poll_interval=30, max_wait=3600):
    """Trigger DAG, monitor cho đến khi hoàn thành."""
    # Pause trước để tránh conflict
    cancel_all_runs(dag_id)

    # Unpause rồi trigger
    set_dag_paused(dag_id, False)
    result = trigger_dag(dag_id)
    if not result:
        print("Failed to trigger DAG")
        return "failed"

    run_id = result.get("dag_run_id") or result.get("run_id")
    if not run_id:
        print(f"Triggered but could not get run_id. Output: {result}")
        return "failed"

    print(f"\nTriggered: {run_id}")
    print(f"Monitoring (poll every {poll_interval}s)...\n")

    start = time.time()
    while time.time() - start < max_wait:
        time.sleep(poll_interval)

        # Tìm run cụ thể đã trigger (không chỉ lấy run đầu tiên)
        runs = list_runs(dag_id, limit=50)
        matched = [r for r in runs if r.get("run_id") == run_id]
        if not matched:
            continue

        state = matched[0].get("state", "unknown")
        tasks = get_task_states(dag_id, run_id)
        success = sum(1 for t in tasks if t.get("state") == "success")
        failed = sum(1 for t in tasks if t.get("state") == "failed")
        running = sum(1 for t in tasks if t.get("state") == "running")
        total = len(tasks)

        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] DAG={state} | tasks: {success}/{total} success, {failed} failed, {running} running")

        if state in ("success", "failed"):
            print(f"\nFinal task states:")
            for t in tasks:
                ts = t.get("state", "?")
                icon = "OK" if ts == "success" else "XX" if ts == "failed" else "--"
                print(f"  [{icon}] {t.get('task_id', '?')}: {ts}")
            return state

    print(f"\nTimeout after {max_wait}s")
    return "timeout"


def main():
    parser = argparse.ArgumentParser(description="Trigger and monitor Airflow DAG (via CLI)")
    parser.add_argument("dag_id", help="DAG ID (e.g. Ethereum)")
    parser.add_argument("--cancel-all", action="store_true", help="Pause DAG and show active runs")
    parser.add_argument("--status", action="store_true", help="Show status of recent runs")
    parser.add_argument("--no-wait", action="store_true", help="Trigger and exit immediately")
    parser.add_argument("--poll-interval", type=int, default=30, help="Poll interval in seconds")
    parser.add_argument("--max-wait", type=int, default=3600, help="Max wait time in seconds")
    args = parser.parse_args()

    # Kiểm tra container đang chạy
    out, rc = run_host_cmd(f"docker ps --filter name={CONTAINER} --format '{{{{.Names}}}}'")
    if CONTAINER not in out:
        print(f"Error: Container '{CONTAINER}' is not running.")
        sys.exit(1)

    if args.cancel_all:
        cancel_all_runs(args.dag_id)
    elif args.status:
        show_status(args.dag_id)
    elif args.no_wait:
        # Pause → unpause → trigger rồi thoát ngay
        cancel_all_runs(args.dag_id)
        set_dag_paused(args.dag_id, False)
        result = trigger_dag(args.dag_id)
        if result:
            run_id = result.get("dag_run_id") or result.get("run_id")
            print(f"Triggered: {run_id}")
            sys.exit(0)
        else:
            print("Failed to trigger DAG")
            sys.exit(1)
    else:
        result = trigger_and_monitor(args.dag_id, args.poll_interval, args.max_wait)
        sys.exit(0 if result == "success" else 1)


if __name__ == "__main__":
    main()
