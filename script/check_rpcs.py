"""
Script to check the RPC list for any EVM chain.

Purpose:
  - Automatically fetch the RPC list from chainlist.org by chain_id or chain name
  - Check whether each RPC satisfies the following 3 requirements:
      1. eth_blockNumber — returns the latest block number
      2. eth_getBlockByNumber — returns full block data (with transactions)
      3. eth_getBlockReceipts — returns the block's receipts (including logs)
  - Print the PASS/FAIL list and the <ENV_VAR>=<rpc1,rpc2,...> string to paste into .env

Input (command-line argument):
  - chain_id (int): chain ID per EIP-155, e.g. 56 (BNB), 1 (Ethereum), 137 (Polygon)
  - Or chain name (str): substring matching the chain name in chainlist.org, e.g. "BNB Smart Chain"

Options:
  --timeout   Per-request timeout (seconds), default 10
  --workers   Number of parallel threads, default 10
  --env-var   Name of the environment variable to print, default inferred from the chain name
              Example: --env-var BNB_RPCS

Output:
  - PASS/FAIL for each RPC
  - Summary counts
  - <ENV_VAR>=... line to copy into .env

Examples:
  python script/check_rpcs.py 56
  python script/check_rpcs.py 1 --env-var ETHEREUM_RPCS
  python script/check_rpcs.py 137 --timeout 15 --workers 20
  python script/check_rpcs.py "BNB Smart Chain"
"""

import argparse
import json
import subprocess
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

CHAINLIST_URL = "https://chainlist.org/rpcs.json"


# ─── RPC validation ───────────────────────────────────────────────────────────

def rpc_call(url: str, method: str, params: list, timeout: int) -> dict:
    """Call a JSON-RPC endpoint and return the response dict."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def has_fields(obj, fields: list) -> tuple:
    """
    Check whether the object has all the required fields.
    Returns (ok: bool, missing: list)
    """
    if not isinstance(obj, dict):
        return False, fields
    missing = [f for f in fields if f not in obj]
    return len(missing) == 0, missing


def check_rpc(url: str, timeout: int) -> tuple:
    """
    Check a single RPC URL in 3 steps.
    Returns (url, passed: bool, reason: str)
    """
    try:
        # Step 1: eth_blockNumber
        resp = rpc_call(url, "eth_blockNumber", [], timeout)
        block_hex = resp.get("result")
        if not block_hex or not isinstance(block_hex, str):
            return url, False, "eth_blockNumber: invalid result"

        # Step 2: eth_getBlockByNumber
        resp2 = rpc_call(url, "eth_getBlockByNumber", [block_hex, True], timeout)
        block = resp2.get("result")
        required_block_fields = [
            "number", "hash",
            "timestamp", "transactions"
        ]
        ok, missing = has_fields(block, required_block_fields)
        if not ok:
            return url, False, f"eth_getBlockByNumber: missing fields {missing}"

        # Check the transactions array (if the block has txs, check the tx fields)
        txs = block.get("transactions", [])
        if isinstance(txs, list) and len(txs) > 0:
            required_tx_fields = [
                "hash", "nonce", "transactionIndex",
                "from", "to", "value", "gasPrice", "gas", "input", "type"
            ]
            ok, missing = has_fields(txs[0], required_tx_fields)
            if not ok:
                return url, False, f"transaction object missing fields {missing}"

        # Step 3: eth_getBlockReceipts
        resp3 = rpc_call(url, "eth_getBlockReceipts", [block_hex], timeout)
        receipts = resp3.get("result")
        if receipts is None:
            return url, False, "eth_getBlockReceipts: result=null (not supported)"
        if not isinstance(receipts, list):
            return url, False, f"eth_getBlockReceipts: result is not an array, got {type(receipts).__name__}"

        # Check the receipt fields (if the block has receipts)
        if len(receipts) > 0:
            required_receipt_fields = [
                "blockHash",
                "from", "gasUsed", "to", "status",
                "transactionHash", "transactionIndex", "logs"
            ]
            ok, missing = has_fields(receipts[0], required_receipt_fields)
            if not ok:
                return url, False, f"receipt object missing fields {missing}"

        return url, True, f"OK (latest block={block_hex})"

    except urllib.error.HTTPError as e:
        return url, False, f"HTTPError: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return url, False, f"URLError: {e.reason}"
    except TimeoutError:
        return url, False, "Timeout"
    except Exception as e:
        return url, False, f"{type(e).__name__}: {e}"


# ─── Chainlist fetching ────────────────────────────────────────────────────────

def fetch_chainlist() -> list:
    """
    Fetch the chain list from chainlist.org/rpcs.json.
    Use curl instead of urllib because chainlist.org blocks Python's default user-agent.
    """
    print("📡 Downloading the chain list from chainlist.org...")
    result = subprocess.run(
        ["curl", "-s", "--max-time", "30", CHAINLIST_URL],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout)


def find_chain(chains: list, identifier: str) -> dict:
    """
    Find a chain by chain_id (number) or name (substring, case-insensitive).
    Raise ValueError if not found or if more than 1 result is found.
    """
    # Try parsing as an integer (chain ID)
    try:
        chain_id = int(identifier)
        matches = [c for c in chains if c.get("chainId") == chain_id]
        if not matches:
            raise ValueError(f"No chain found with chainId={chain_id}")
        return matches[0]
    except ValueError as e:
        # If the error was raised by us, re-raise it
        if "No chain found" in str(e):
            raise

    # Search by name (substring, case-insensitive)
    name_lower = identifier.lower()
    matches = [c for c in chains if name_lower in c.get("name", "").lower()]
    if not matches:
        raise ValueError(f"No chain found with a name containing '{identifier}'")
    if len(matches) > 1:
        names = [f"  chainId={c['chainId']}: {c['name']}" for c in matches]
        raise ValueError(
            f"Found {len(matches)} chains matching '{identifier}'. Use a chainId instead:\n"
            + "\n".join(names)
        )
    return matches[0]


def extract_free_rpcs(chain: dict) -> list:
    """Get the list of free HTTPS RPCs (no API key required) from the chain object."""
    rpcs = []
    for rpc in chain.get("rpc", []):
        url = rpc.get("url", "") if isinstance(rpc, dict) else rpc
        # Only keep HTTPS, skip URLs containing a placeholder key of the form ${...}
        if url.startswith("https://") and "${" not in url:
            rpcs.append(url)
    return rpcs


def infer_env_var(chain_name: str) -> str:
    """
    Infer the environment variable name from the chain name.
    Examples: "BNB Smart Chain Mainnet" → "BNB_RPCS"
              "Ethereum Mainnet"        → "ETHEREUM_RPCS"
              "Polygon Mainnet"         → "POLYGON_RPCS"
    """
    first_word = chain_name.strip().split()[0].upper()
    # Remove special characters
    first_word = "".join(c for c in first_word if c.isalnum())
    return f"{first_word}_RPCS"


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Check RPC endpoints of an EVM chain from chainlist.org"
    )
    parser.add_argument(
        "chain",
        help="Chain ID (number) or chain name (substring). Examples: 56, 1, 137, 'BNB Smart Chain'"
    )
    parser.add_argument(
        "--timeout", type=int, default=10,
        help="Per-request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--workers", type=int, default=10,
        help="Number of parallel check threads (default: 10)"
    )
    parser.add_argument(
        "--env-var", dest="env_var", default=None,
        help="Name of the environment variable to print (default: inferred from the chain name)"
    )
    args = parser.parse_args()

    # Get chain info
    try:
        chains = fetch_chainlist()
        chain = find_chain(chains, args.chain)
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    chain_name = chain["name"]
    chain_id = chain["chainId"]
    rpc_list = extract_free_rpcs(chain)
    env_var = args.env_var or infer_env_var(chain_name)

    print(f"🔗 Chain: {chain_name} (chainId={chain_id})")
    print(f"📋 Found {len(rpc_list)} free HTTPS RPCs")
    print(f"🔑 Environment variable: {env_var}")
    print(f"⏱  Timeout: {args.timeout}s | Workers: {args.workers}")
    print("=" * 70)

    passed = []
    failed = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(check_rpc, url, args.timeout): url
            for url in rpc_list
        }
        for future in as_completed(futures):
            url, ok, reason = future.result()
            status = "✅ PASS" if ok else "❌ FAIL"
            print(f"{status} | {url}")
            if not ok:
                print(f"       Reason: {reason}")
            if ok:
                passed.append(url)
            else:
                failed.append((url, reason))

    print("\n" + "=" * 70)
    print(f"\n📊 Results: {len(passed)} PASS / {len(failed)} FAIL / {len(rpc_list)} total\n")

    if not passed:
        print("⚠️  No RPC passed!", file=sys.stderr)
        sys.exit(1)

    print("✅ RPCs meeting the requirements:")
    for url in passed:
        print(f"   {url}")
    print()
    print(f"# Add the following line to chainslake-run/.env:")
    print(f"{env_var}=" + ",".join(passed))


if __name__ == "__main__":
    main()
