"""
Chạy một job pipeline trực tiếp qua docker exec (thay vì chạy thủ công).

Agent có thể dùng script này để chạy bất kỳ job nào trong
`chainslake/jobs/<chain>/<category>/<job>.sh` mà không cần tự soạn
lệnh `docker exec ...` phức tạp. Output của job được stream trực tiếp
ra terminal (in dòng theo thời gian thực), exit code trả về bằng exit
code của job bên trong container.

Usage:
    python script/run_job.py ethereum/extract/blocks.sh
    python script/run_job.py ethereum.extract.blocks
    python script/run_job.py blocks --chain ethereum
    python script/run_job.py --list
    python script/run_job.py ethereum --list
    python script/run_job.py ethereum/extract/blocks.sh --dry-run
"""

import argparse
import os
import shlex
import subprocess
import sys

from pathlib import Path

# Host path mapping: mount trong docker-compose
HOST_CHAINSLAKE = Path("/home/long/projects/chainslake-onprem/chainslake")
CONTAINER = "chainslake-onprem-node01-1"
USER = "hadoop"

# Path trong container
CT_CHAINSLAKE = "/home/hadoop/projects/chainslake"
CT_JOBS = f"{CT_CHAINSLAKE}/jobs"

# Các category chuẩn của pipeline
CATEGORIES = ["origin", "extract", "decoded", "contract", "token"]

# Path trong container nơi .env của chainslake-run nằm (đã có sẵn trong container)
CT_RUN_DIR = "/home/hadoop/projects/chainslake-run"


def resolve_job(job_ref, chain=None):
    """
    Phân tích job reference thành (chain, category, job_name, sh_path_host).

    Hỗ trợ các format:
      - ethereum/extract/blocks.sh
      - ethereum/extract/blocks
      - ethereum.extract.blocks
      - blocks --chain ethereum   (nếu --chain được truyền)
    """
    ref = job_ref.strip()
    parts = None

    if "/" in ref:
        parts = [p for p in ref.split("/") if p]
    elif "." in ref:
        parts = [p for p in ref.split(".") if p]
    else:
        parts = [ref]

    # Bỏ đuôi .sh
    if parts and parts[-1].endswith(".sh"):
        parts[-1] = parts[-1][:-3]

    if not parts:
        return None

    # Nếu chỉ có 1 phần và --chain được truyền → tên job, tìm category sau
    if len(parts) == 1 and chain:
        return {
            "chain": chain,
            "category": None,
            "job": parts[0],
        }

    # ethereum/extract/blocks → [chain, category, job]
    if len(parts) == 3:
        return {
            "chain": parts[0],
            "category": parts[1],
            "job": parts[2],
        }

    # ethereum/origin → [chain, category] (job tự suy ra nếu category chỉ có 1 file)
    if len(parts) == 2 and parts[0] in _existing_chains():
        return {
            "chain": parts[0],
            "category": parts[1],
            "job": None,
        }

    # extract/blocks → cần --chain
    if len(parts) == 2 and chain:
        return {
            "chain": chain,
            "category": parts[0],
            "job": parts[1],
        }

    return None


def _existing_chains():
    jobs_root = HOST_CHAINSLAKE / "jobs"
    if not jobs_root.is_dir():
        return []
    return sorted(d.name for d in jobs_root.iterdir() if d.is_dir())


def find_job_sh(job_info):
    """Tìm file .sh thực tế của job trên host."""
    chain = job_info["chain"]
    category = job_info["category"]
    job = job_info["job"]

    jobs_dir = HOST_CHAINSLAKE / "jobs" / chain
    if not jobs_dir.exists():
        print(f"Error: không tìm thấy thư mục jobs: {jobs_dir}")
        return None

    # Nếu job chưa xác định (chỉ có category), tìm file duy nhất trong category
    if not job:
        cat_dir = jobs_dir / category
        if not cat_dir.exists():
            print(f"Error: không tìm thấy category: {cat_dir}")
            return None
        sh_files = sorted(cat_dir.glob("*.sh"))
        if len(sh_files) != 1:
            print(f"Error: category '{category}' có {len(sh_files)} job scripts, cần chỉ định rõ job:")
            for f in sh_files:
                print(f"  - {f.stem}")
            return None
        job = sh_files[0].stem
        job_info["job"] = job

    # Nếu category chưa xác định (chỉ truyền tên job), tìm trong mọi category
    if not category:
        for cat in CATEGORIES:
            cand = jobs_dir / cat / f"{job}.sh"
            if cand.is_file():
                job_info["category"] = cat
                return cand
        print(f"Error: không tìm thấy job '{job}' trong bất kỳ category nào của {jobs_dir}")
        return None

    candidates = [
        jobs_dir / category / f"{job}.sh",
        jobs_dir / category / f"{job}",
        jobs_dir / job / f"{job}.sh",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand

    print(f"Error: không tìm thấy job script '{job}' trong {jobs_dir / category}")
    return None


def build_remote_cmd(job_info):
    """
    Build command chạy job bên trong container:
      cd <CT_JOBS>/<chain> && ./<category>/<job>.sh
    """
    chain = job_info["chain"]
    category = job_info["category"]
    job = job_info["job"]
    return f"cd {CT_JOBS}/{chain} && ./{category}/{job}.sh"


def run_job(job_info, timeout=None, dry_run=False):
    """Chạy job bên trong container, stream output, trả exit code."""
    remote_cmd = build_remote_cmd(job_info)

    full_cmd = (
        f"export PS1='something' && source /etc/bash.bashrc && "
        f"cd {CT_JOBS}/{job_info['chain']} && "
        f"./{job_info['category']}/{job_info['job']}.sh"
    )

    docker_cmd = [
        "docker", "exec", "-u", USER, CONTAINER,
        "bash", "-c", full_cmd,
    ]

    print(f"  Container : {CONTAINER}")
    print(f"  User      : {USER}")
    print(f"  Command   : {remote_cmd}")
    print(f"  Timeout   : {timeout or 'none'}")
    print(f"{'=' * 60}")

    if dry_run:
        print("  [DRY RUN] Lệnh docker sẽ chạy:")
        print("  " + shlex.join(docker_cmd))
        return 0

    try:
        proc = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        print("Error: không tìm thấy 'docker' trên host.")
        return 1

    start = None
    if timeout:
        import time
        start = time.time()

    try:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if timeout and time.time() - start > timeout:
                print(f"\nError: timeout sau {timeout}s, kill job.")
                proc.kill()
                proc.wait()
                return 124
    except KeyboardInterrupt:
        print("\nInterrupted, kill job...")
        proc.kill()
        proc.wait()
        return 130

    rc = proc.wait()
    return rc


def list_jobs(chain=None):
    """Liệt kê tất cả job scripts có sẵn."""
    jobs_root = HOST_CHAINSLAKE / "jobs"
    chains = [chain] if chain else sorted(d.name for d in jobs_root.iterdir() if d.is_dir())

    found = 0
    for ch in chains:
        ch_dir = jobs_root / ch
        if not ch_dir.is_dir():
            print(f"  (chain '{ch}' không tồn tại)")
            continue
        print(f"\n[{ch}]")
        for cat in CATEGORIES:
            cat_dir = ch_dir / cat
            if not cat_dir.is_dir():
                continue
            sh_files = sorted(cat_dir.glob("*.sh"))
            if not sh_files:
                continue
            print(f"  {cat}/")
            for f in sh_files:
                print(f"    - {f.stem}")
                found += 1
    if found == 0:
        print("  (không có job nào)")
    return found


def main():
    parser = argparse.ArgumentParser(
        description="Chạy job pipeline qua docker exec (thay cho chạy thủ công)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ví dụ:\n"
            "  python script/run_job.py ethereum/extract/blocks.sh\n"
            "  python script/run_job.py ethereum.extract.blocks\n"
            "  python script/run_job.py blocks --chain ethereum\n"
            "  python script/run_job.py --list\n"
        ),
    )
    parser.add_argument("job", nargs="?", help="Job reference, ví dụ: ethereum/extract/blocks.sh hoặc ethereum.extract.blocks")
    parser.add_argument("--chain", help="Tên chain (cần khi job_ref không có chain)")
    parser.add_argument("--list", action="store_true", help="Liệt kê tất cả job scripts có sẵn")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in lệnh docker sẽ chạy, không thực thi")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout (giây), kill job nếu quá lâu")
    args = parser.parse_args()

    # Kiểm tra container đang chạy
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={CONTAINER}", "--format", "{{.Names}}"],
        capture_output=True, text=True,
    )
    if CONTAINER not in result.stdout:
        print(f"Error: container '{CONTAINER}' không đang chạy. Hãy `docker compose up -d` trước.")
        sys.exit(1)

    if args.list:
        list_jobs(args.chain)
        sys.exit(0)

    if not args.job:
        parser.print_help()
        sys.exit(1)

    job_info = resolve_job(args.job, args.chain)
    if not job_info:
        print(f"Error: không parse được job reference '{args.job}'.")
        print("  Format hợp lệ: ethereum/extract/blocks.sh | ethereum.extract.blocks | extract/blocks --chain ethereum")
        sys.exit(1)

    sh_path = find_job_sh(job_info)
    if sh_path is None:
        sys.exit(1)

    print(f"\n==> Chuẩn bị chạy job: {sh_path}")
    rc = run_job(job_info, timeout=args.timeout, dry_run=args.dry_run)

    print(f"{'=' * 60}")
    print(f"Job {'thành công' if rc == 0 else f'kết thúc với exit code {rc}'}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
