"""
Run a pipeline job directly via docker exec (instead of manual execution).

Agents can use this script to run any job in
`chainslake/jobs/<chain>/<category>/<job>.sh` without manually composing
complex `docker exec ...` commands. Job output is streamed directly
to the terminal (printed in real-time), exit code is returned as the
exit code of the job inside the container.

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

# Container path
CT_CHAINSLAKE = "/home/hadoop/projects/chainslake"
CT_JOBS = f"{CT_CHAINSLAKE}/jobs"

# Standard pipeline categories
CATEGORIES = ["origin", "extract", "decoded", "contract", "token"]

# Container path where chainslake-run .env is located (already available in container)
CT_RUN_DIR = "/home/hadoop/projects/chainslake-run"


def resolve_job(job_ref, chain=None):
    """
    Parse job reference into (chain, category, job_name, sh_path_host).

    Supported formats:
      - ethereum/extract/blocks.sh
      - ethereum/extract/blocks
      - ethereum.extract.blocks
      - blocks --chain ethereum   (if --chain is provided)
    """
    ref = job_ref.strip()
    parts = None

    if "/" in ref:
        parts = [p for p in ref.split("/") if p]
    elif "." in ref:
        parts = [p for p in ref.split(".") if p]
    else:
        parts = [ref]

    # Strip .sh suffix
    if parts and parts[-1].endswith(".sh"):
        parts[-1] = parts[-1][:-3]

    if not parts:
        return None

    # If only 1 part and --chain is provided → job name, find category after
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

    # ethereum/origin → [chain, category] (job auto-inferred if category has only 1 file)
    if len(parts) == 2 and parts[0] in _existing_chains():
        return {
            "chain": parts[0],
            "category": parts[1],
            "job": None,
        }

    # extract/blocks → needs --chain
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
    """Find the actual .sh file of the job on the host."""
    chain = job_info["chain"]
    category = job_info["category"]
    job = job_info["job"]

    jobs_dir = HOST_CHAINSLAKE / "jobs" / chain
    if not jobs_dir.exists():
        print(f"Error: jobs directory not found: {jobs_dir}")
        return None

    # If job not determined (only category), find the single file in category
    if not job:
        cat_dir = jobs_dir / category
        if not cat_dir.exists():
            print(f"Error: category not found: {cat_dir}")
            return None
        sh_files = sorted(cat_dir.glob("*.sh"))
        if len(sh_files) != 1:
            print(f"Error: category '{category}' has {len(sh_files)} job scripts, please specify a job:")
            for f in sh_files:
                print(f"  - {f.stem}")
            return None
        job = sh_files[0].stem
        job_info["job"] = job

    # If category not determined (only job name passed), search in all categories
    if not category:
        for cat in CATEGORIES:
            cand = jobs_dir / cat / f"{job}.sh"
            if cand.is_file():
                job_info["category"] = cat
                return cand
        print(f"Error: job '{job}' not found in any category of {jobs_dir}")
        return None

    candidates = [
        jobs_dir / category / f"{job}.sh",
        jobs_dir / category / f"{job}",
        jobs_dir / job / f"{job}.sh",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand

    print(f"Error: job script '{job}' not found in {jobs_dir / category}")
    return None


def build_remote_cmd(job_info):
    """
    Build command to run job inside container:
      cd <CT_JOBS>/<chain> && ./<category>/<job>.sh
    """
    chain = job_info["chain"]
    category = job_info["category"]
    job = job_info["job"]
    return f"cd {CT_JOBS}/{chain} && ./{category}/{job}.sh"


def run_job(job_info, timeout=None, dry_run=False):
    """Run job inside container, stream output, return exit code."""
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
        print("  [DRY RUN] Docker command to be executed:")
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
        print("Error: 'docker' not found on host.")
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
                print(f"\nError: timeout after {timeout}s, killing job.")
                proc.kill()
                proc.wait()
                return 124
    except KeyboardInterrupt:
        print("\nInterrupted, killing job...")
        proc.kill()
        proc.wait()
        return 130

    rc = proc.wait()
    return rc


def list_jobs(chain=None):
    """List all available job scripts."""
    jobs_root = HOST_CHAINSLAKE / "jobs"
    chains = [chain] if chain else sorted(d.name for d in jobs_root.iterdir() if d.is_dir())

    found = 0
    for ch in chains:
        ch_dir = jobs_root / ch
        if not ch_dir.is_dir():
            print(f"  (chain '{ch}' does not exist)")
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
        print("  (no jobs found)")
    return found


def main():
    parser = argparse.ArgumentParser(
        description="Run pipeline job via docker exec (instead of manual execution)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python script/run_job.py ethereum/extract/blocks.sh\n"
            "  python script/run_job.py ethereum.extract.blocks\n"
            "  python script/run_job.py blocks --chain ethereum\n"
            "  python script/run_job.py --list\n"
        ),
    )
    parser.add_argument("job", nargs="?", help="Job reference, e.g.: ethereum/extract/blocks.sh or ethereum.extract.blocks")
    parser.add_argument("--chain", help="Chain name (needed when job_ref doesn't include chain)")
    parser.add_argument("--list", action="store_true", help="List all available job scripts")
    parser.add_argument("--dry-run", action="store_true", help="Print docker command without executing")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout (seconds), kill job if exceeded")
    args = parser.parse_args()

    # Check if container is running
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={CONTAINER}", "--format", "{{.Names}}"],
        capture_output=True, text=True,
    )
    if CONTAINER not in result.stdout:
        print(f"Error: container '{CONTAINER}' is not running. Please run `docker compose up -d` first.")
        sys.exit(1)

    if args.list:
        list_jobs(args.chain)
        sys.exit(0)

    if not args.job:
        parser.print_help()
        sys.exit(1)

    job_info = resolve_job(args.job, args.chain)
    if not job_info:
        print(f"Error: cannot parse job reference '{args.job}'.")
        print("  Valid formats: ethereum/extract/blocks.sh | ethereum.extract.blocks | extract/blocks --chain ethereum")
        sys.exit(1)

    sh_path = find_job_sh(job_info)
    if sh_path is None:
        sys.exit(1)

    print(f"\n==> Preparing to run job: {sh_path}")
    rc = run_job(job_info, timeout=args.timeout, dry_run=args.dry_run)

    print(f"{'=' * 60}")
    print(f"Job {'succeeded' if rc == 0 else f'ended with exit code {rc}'}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
