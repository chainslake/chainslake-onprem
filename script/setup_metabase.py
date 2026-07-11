"""
Setup Metabase on-premise: tạo admin account, kết nối SparkSQL và Trino.

Đọc credentials từ script/.env (xem script/env_example).

Usage:
    python script/setup_metabase.py [--skip-databases]
"""

import argparse
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv("script/.env")


def wait_for_metabase(base_url, timeout=120):
    """Đợi Metabase sẵn sàng."""
    print("[1/4] Waiting for Metabase to be ready...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{base_url}/api/health", timeout=5)
            if r.status_code == 200 and r.json().get("status") == "ok":
                print("  Metabase is ready!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(3)
    print(f"  ERROR: Metabase not ready after {timeout}s")
    return False


def check_already_setup(base_url):
    """Kiểm tra xem Metabase đã có admin chưa."""
    r = requests.get(f"{base_url}/api/session/properties", timeout=10)
    if r.status_code == 200:
        return r.json().get("has-user-setup", False)
    return False


def setup_admin(base_url, email, password, site_name):
    """Tạo admin account qua /api/setup."""
    print("[2/4] Setting up admin account...")

    props = requests.get(f"{base_url}/api/session/properties", timeout=10).json()
    token = props.get("setup-token")
    if not token:
        print("  ERROR: No setup-token available. Metabase may already be set up.")
        return None

    payload = {
        "token": token,
        "user": {
            "email": email,
            "first_name": "Admin",
            "last_name": "User",
            "password": password,
        },
        "prefs": {
            "site_name": site_name,
            "site_locale": "en",
        },
        "database": None,
    }

    r = requests.post(f"{base_url}/api/setup", json=payload, timeout=15)
    if r.status_code == 200:
        session_id = r.json().get("id")
        print(f"  Admin created! Session: {session_id[:12]}...")
        return session_id
    else:
        print(f"  ERROR: {r.status_code} — {r.text[:200]}")
        return None


def login(base_url, email, password):
    """Login và trả về session token."""
    print("[2/4] Logging in...")
    r = requests.post(
        f"{base_url}/api/session",
        json={"username": email, "password": password},
        timeout=10,
    )
    if r.status_code == 200:
        session_id = r.json().get("id")
        print(f"  Logged in! Session: {session_id[:12]}...")
        return session_id
    else:
        print(f"  ERROR: {r.status_code} — {r.text[:200]}")
        return None


def create_api_key(base_url, session_id, key_name="chainslake-agent"):
    """Tạo API key cho automation."""
    print("[3/4] Creating API key...")
    headers = {"Content-Type": "application/json", "X-Metabase-Session": session_id}
    r = requests.post(
        f"{base_url}/api/api-key",
        headers=headers,
        json={"name": key_name, "group_id": 1},
        timeout=10,
    )
    if r.status_code == 200:
        key = r.json().get("unmasked_key")
        print(f"  API key created: {key[:15]}...")
        return key
    else:
        print(f"  ERROR: {r.status_code} — {r.text[:200]}")
        return None


def add_database(base_url, session_id, engine, name, details):
    """Thêm database connection."""
    headers = {"Content-Type": "application/json", "X-Metabase-Session": session_id}
    payload = {
        "engine": engine,
        "name": name,
        "details": details,
        "is_full_sync": True,
        "schedules": {},
    }
    r = requests.post(f"{base_url}/api/database", headers=headers, json=payload, timeout=30)
    if r.status_code == 200:
        print(f"  [{name}] Added successfully")
        return True
    else:
        print(f"  [{name}] Failed: {r.status_code} — {r.text[:200]}")
        return False


def add_databases(base_url, session_id):
    """Thêm SparkSQL và Trino."""
    print("[4/4] Adding database connections...")

    add_database(base_url, session_id, "sparksql", "Spark", {
        "host": "node01",
        "port": 10000,
        "database": "default",
        "user": "hadoop",
        "password": "hadooppass",
    })

    add_database(base_url, session_id, "starburst", "Trino", {
        "host": "node01",
        "port": 8889,
        "catalog": "hive",
        "user": "metabase",
        "ssl": False,
    })


def main():
    parser = argparse.ArgumentParser(description="Setup Metabase on-premise")
    parser.add_argument("--skip-databases", action="store_true", help="Skip adding databases")
    parser.add_argument("--api-key-file", default="query/.env", help="Path to write API key .env")
    args = parser.parse_args()

    base_url = os.getenv("METABASE_URL", "http://localhost:53000")
    email = os.getenv("METABASE_EMAIL")
    password = os.getenv("METABASE_PASSWORD")
    site_name = os.getenv("METABASE_SITE_NAME", "Chainslake Warehouse")

    if not email or not password:
        print("ERROR: METABASE_EMAIL and METABASE_PASSWORD must be set in script/.env")
        print("Copy script/env_example to script/.env and fill in credentials.")
        sys.exit(1)

    # Step 1: Wait
    if not wait_for_metabase(base_url):
        sys.exit(1)

    # Step 2: Setup or Login
    session_id = None
    if check_already_setup(base_url):
        print("[2/4] Already set up, logging in...")
        session_id = login(base_url, email, password)
    else:
        session_id = setup_admin(base_url, email, password, site_name)
        if not session_id:
            session_id = login(base_url, email, password)

    if not session_id:
        print("FATAL: Cannot authenticate with Metabase")
        sys.exit(1)

    # Step 3: API key
    api_key = create_api_key(base_url, session_id)
    if api_key and args.api_key_file:
        os.makedirs(os.path.dirname(args.api_key_file) or ".", exist_ok=True)
        with open(args.api_key_file, "w") as f:
            f.write(f"METABASE_API_KEY={api_key}\n")
        print(f"  Wrote {args.api_key_file}")

    # Step 4: Databases
    if not args.skip_databases:
        add_databases(base_url, session_id)

    print("\nSetup complete!")
    print(f"  URL:      {base_url}")
    print(f"  Email:    {email}")


if __name__ == "__main__":
    main()
