"""
Trigger và theo dõi Airflow DAG run.

Đọc credentials từ script/.env (xem script/env_example).
Login qua CSRF form-based auth (không phải REST API auth).

Usage:
    python script/trigger_dag.py Ethereum                          # trigger + monitor
    python script/trigger_dag.py Ethereum --cancel-all
    python script/trigger_dag.py Ethereum --status
    python script/trigger_dag.py Ethereum --no-wait
"""

import argparse
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv("script/.env")


def get_airflow_password(password_file):
    """Đọc admin password từ file."""
    with open(password_file, "r") as f:
        return f.read().strip()


class AirflowClient:
    """Airflow REST API client with CSRF-based login."""

    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.session = requests.Session()
        self._login(password)

    def _login(self, password):
        """Login via form POST với CSRF token."""
        resp = self.session.get(f"{self.base_url}/login/", timeout=10)
        csrf_match = re.search(
            r'name="csrf_token"[^>]*value="([^"]+)"', resp.text
        )
        if not csrf_match:
            raise RuntimeError("Cannot find CSRF token on login page")

        csrf = csrf_match.group(1)
        login_resp = self.session.post(
            f"{self.base_url}/login/",
            data={"username": self.username, "password": password, "csrf_token": csrf},
            allow_redirects=False,
            timeout=10,
        )
        if login_resp.status_code != 302:
            raise RuntimeError(f"Login failed: {login_resp.status_code}")

    def list_dags(self, limit=50):
        r = self.session.get(f"{self.base_url}/api/v1/dags?limit={limit}", timeout=10)
        r.raise_for_status()
        return r.json().get("dags", [])

    def get_dag_runs(self, dag_id, limit=10):
        r = self.session.get(
            f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns?limit={limit}", timeout=10
        )
        r.raise_for_status()
        return r.json().get("dag_runs", [])

    def get_task_instances(self, dag_id, run_id):
        r = self.session.get(
            f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances",
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("task_instances", [])

    def trigger_dag(self, dag_id, conf=None):
        r = self.session.post(
            f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns",
            json={"conf": conf or {}},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def cancel_dag_run(self, dag_id, run_id):
        r = self.session.delete(
            f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns/{run_id}", timeout=10
        )
        return r.status_code

    def set_dag_paused(self, dag_id, paused):
        r = self.session.patch(
            f"{self.base_url}/api/v1/dags/{dag_id}",
            json={"is_paused": paused},
            timeout=10,
        )
        r.raise_for_status()

    def get_task_log(self, dag_id, run_id, task_id, try_number=1):
        r = self.session.get(
            f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns/{run_id}"
            f"/taskInstances/{task_id}/logs/{try_number}",
            timeout=15,
        )
        if r.status_code == 200:
            return r.text
        return None


def cancel_all_runs(client, dag_id):
    runs = client.get_dag_runs(dag_id, limit=20)
    cancelled = 0
    for r in runs:
        if r["state"] in ("running", "queued"):
            status = client.cancel_dag_run(dag_id, r["dag_run_id"])
            if status in (200, 204):
                print(f"  Cancelled: {r['dag_run_id']}")
                cancelled += 1
    if cancelled == 0:
        print("  No running/queued runs to cancel.")
    return cancelled


def show_status(client, dag_id):
    runs = client.get_dag_runs(dag_id, limit=5)
    if not runs:
        print(f"No runs found for DAG '{dag_id}'")
        return

    for r in runs:
        run_id = r["dag_run_id"]
        state = r["state"]
        print(f"\n{'='*60}")
        print(f"Run:  {run_id}")
        print(f"State: {state}")

        tasks = client.get_task_instances(dag_id, run_id)
        for t in tasks:
            icon = {"success": "OK", "failed": "XX", "running": "..", "queued": ".."}.get(
                t["state"], "--"
            )
            print(f"  [{icon}] {t['task_id']}: {t['state']} (try={t['try_number']})")


def trigger_and_monitor(client, dag_id, poll_interval=30, max_wait=3600):
    cancel_all_runs(client, dag_id)
    client.set_dag_paused(dag_id, False)

    result = client.trigger_dag(dag_id)
    run_id = result["dag_run_id"]
    print(f"\nTriggered: {run_id}")
    print(f"Monitoring (poll every {poll_interval}s)...\n")

    start = time.time()
    while time.time() - start < max_wait:
        time.sleep(poll_interval)

        runs = client.get_dag_runs(dag_id, limit=1)
        if not runs:
            continue

        state = runs[0]["state"]
        tasks = client.get_task_instances(dag_id, run_id)
        success = sum(1 for t in tasks if t["state"] == "success")
        failed = sum(1 for t in tasks if t["state"] == "failed")
        running = sum(1 for t in tasks if t["state"] == "running")
        total = len(tasks)

        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] DAG={state} | tasks: {success}/{total} success, {failed} failed, {running} running")

        if state in ("success", "failed"):
            print(f"\nFinal task states:")
            for t in tasks:
                icon = "OK" if t["state"] == "success" else "XX" if t["state"] == "failed" else "--"
                print(f"  [{icon}] {t['task_id']}: {t['state']}")
            return state

    print(f"\nTimeout after {max_wait}s")
    return "timeout"


def main():
    parser = argparse.ArgumentParser(description="Trigger and monitor Airflow DAG")
    parser.add_argument("dag_id", help="DAG ID (e.g. Ethereum)")
    parser.add_argument(
        "--password-file",
        default="chainslake/airflow/standalone_admin_password.txt",
        help="Path to Airflow admin password file",
    )
    parser.add_argument("--cancel-all", action="store_true", help="Cancel all running/queued runs")
    parser.add_argument("--status", action="store_true", help="Show status of recent runs")
    parser.add_argument("--no-wait", action="store_true", help="Trigger and exit immediately")
    parser.add_argument("--poll-interval", type=int, default=30, help="Poll interval in seconds")
    parser.add_argument("--max-wait", type=int, default=3600, help="Max wait time in seconds")
    args = parser.parse_args()

    airflow_url = os.getenv("AIRFLOW_URL", "http://localhost:58080")
    airflow_username = os.getenv("AIRFLOW_USERNAME", "admin")
    airflow_password = get_airflow_password(args.password_file)

    client = AirflowClient(airflow_url, airflow_username, airflow_password)

    if args.cancel_all:
        cancel_all_runs(client, args.dag_id)
    elif args.status:
        show_status(client, args.dag_id)
    else:
        result = trigger_and_monitor(client, args.dag_id, args.poll_interval, args.max_wait)
        sys.exit(0 if result == "success" else 1)


if __name__ == "__main__":
    main()
