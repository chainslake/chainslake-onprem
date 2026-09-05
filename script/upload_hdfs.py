"""
Upload CSV files from the local `chainslake/ext_upload/` directory into HDFS,
and create the target directory if it does not exist.

This wraps the `hdfs dfs` commands inside the container (via docker exec) so
that agents do NOT need to call `docker exec` directly.

Usage:
    python script/upload_hdfs.py <schema>.<table> <file_name.csv>
    python script/upload_hdfs.py ext_upload eth_etf_address.csv
    python script/upload_hdfs.py <schema>.<table> <file_name.csv> --no-mkdir
    python script/upload_hdfs.py <schema>.<table> <file_name.csv> --dry-run
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Host path mapping (mount trong docker-compose)
HOST_CHAINSLAKE = Path("/home/long/projects/chainslake-onprem/chainslake")
CONTAINER = "chainslake-onprem-node01-1"
USER = "hadoop"

# Container paths
CT_EXT_UPLOAD = "/home/hadoop/projects/chainslake/ext_upload"
CT_WAREHOUSE = "/user/hive/warehouse"  # relative to hdfs root


def build_hdfs_cmd(commands):
    """Build a single docker exec command running hdfs dfs on the container."""
    joined = " && ".join(commands)
    full_cmd = (
        f"export PS1='something' && source /etc/bash.bashrc && "
        f"{joined}"
    )
    return [
        "docker", "exec", "-u", USER, CONTAINER,
        "bash", "-c", full_cmd,
    ]


def check_container():
    """Return True if container is running."""
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={CONTAINER}", "--format", "{{.Names}}"],
        capture_output=True, text=True,
    )
    return CONTAINER in result.stdout


def upload(schema_table, file_name, mkdir=True, dry_run=False):
    """Create HDFS dir + upload file. Return exit code."""
    parts = schema_table.strip().split(".")
    if len(parts) != 2:
        print(f"Error: schema.table must have exactly 2 parts, got '{schema_table}'")
        return 1
    schema, table = parts

    local_file = HOST_CHAINSLAKE / "ext_upload" / file_name
    if not local_file.is_file():
        print(f"Error: file not found on host: {local_file}")
        print("  Place the CSV in `chainslake/ext_upload/` first.")
        return 1

    hdfs_dir = f"{CT_WAREHOUSE}/{schema}.db/{table}"

    commands = []
    if mkdir:
        commands.append(f"hdfs dfs -mkdir -p {hdfs_dir}")
    commands.append(f"hdfs dfs -put {CT_EXT_UPLOAD}/{file_name} {hdfs_dir}/")

    print(f"  Container : {CONTAINER}")
    print(f"  File      : {local_file}")
    print(f"  HDFS dir  : {hdfs_dir}")
    print(f"  Commands  : {' && '.join(commands)}")
    print("=" * 60)

    cmd = build_hdfs_cmd(commands)
    if dry_run:
        print("  [DRY RUN] Docker command to be executed:")
        print("  " + " ".join(cmd))
        return 0

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        print("Error: 'docker' not found on host.")
        return 1

    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

    rc = proc.wait()
    if rc == 0:
        print("=" * 60)
        print("Upload succeeded.")
    else:
        print("=" * 60)
        print(f"Upload failed with exit code {rc}")
    return rc


def main():
    parser = argparse.ArgumentParser(
        description="Upload CSV from chainslake/ext_upload/ to HDFS (wraps docker exec)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python script/upload_hdfs.py ext_upload eth_etf_address.csv\n"
            "  python script/upload_hdfs.py ext_upload eth_etf_address.csv --dry-run\n"
        ),
    )
    parser.add_argument("schema_table", help="Target table: <schema>.<table> (e.g. ext_upload.eth_etf_address)")
    parser.add_argument("file_name", help="CSV file name inside chainslake/ext_upload/ (e.g. eth_etf_address.csv)")
    parser.add_argument("--no-mkdir", action="store_true", help="Skip creating the HDFS directory")
    parser.add_argument("--dry-run", action="store_true", help="Print docker command without executing")
    args = parser.parse_args()

    if not check_container():
        print(f"Error: container '{CONTAINER}' is not running. Please run `docker compose up -d` first.")
        sys.exit(1)

    sys.exit(upload(args.schema_table, args.file_name, mkdir=not args.no_mkdir, dry_run=args.dry_run))


if __name__ == "__main__":
    main()