"""
Script to check RPC endpoints for any EVM chain.

Purpose:
  - Automatically fetch RPC list from chainlist.org by chain_id or chain name
  - Check each RPC against 3 requirements:
      1. eth_blockNumber — return latest block number
      2. eth_getBlockByNumber — return full block data (with transactions)
      3. eth_getBlockReceipts — return block receipts (including logs)
  - Print PASS/FAIL list and <ENV_VAR>=<rpc1,rpc2,...> string to paste into .env

Input (CLI argument):
  - chain_id (int): chain ID per EIP-155, e.g. 56 (BNB), 1 (Ethereum), 137 (Polygon)
  - Or chain name (str): substring matching chain name on chainlist.org, e.g. "BNB Smart Chain"

Options:
  --timeout   Timeout per request (seconds), default 10
  --workers   Number of parallel threads, default 10
  --env-var   Environment variable name to print, default auto-inferred from chain name
              e.g.: --env-var BNB_RPCS

Output:
  - PASS/FAIL per RPC
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
    """Call JSON-RPC endpoint and return response dict."""
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
    Check if object has all required fields.
    Returns (ok: bool, missing: list)
    """
    if not isinstance(obj, dict):
        return False, fields
    missing = [f for f in fields if f not in obj]
    return len(missing) == 0, missing


def check_rpc(url: str, timeout: int) -> tuple:
    """
    Check an RPC URL in 3 steps.
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

        # Check transactions array (if block has txs, check tx fields)
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

        # Check receipt fields (if block has receipts)
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
    Fetch chain list from chainlist.org/rpcs.json.
    Uses curl instead of urllib because chainlist.org blocks Python's default user-agent.
    """
    print("Fetching chain list from chainlist.org...")
    result = subprocess.run(
        ["curl", "-s", "--max-time", "30", CHAINLIST_URL],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout)


def find_chain(chains: list, identifier: str) -> dict:
    """
    Find chain by chain_id (number) or name (substring, case-insensitive).
    Raises ValueError if not found or more than 1 match.
    """
    # Try parsing as integer (chain ID)
    try:
        chain_id = int(identifier)
        matches = [c for c in chains if c.get("chainId") == chain_id]
        if not matches:
            raise ValueError(f"No chain found with chainId={chain_id}")
        return matches[0]
    except ValueError as e:
        # If error was raised by us, re-raise
        if "No chain found" in str(e):
            raise

    # Search by name (substring, case-insensitive)
    name_lower = identifier.lower()
    matches = [c for c in chains if name_lower in c.get("name", "").lower()]
    if not matches:
        raise ValueError(f"No chain found with name containing '{identifier}'")
    if len(matches) > 1:
        names = [f"  chainId={c['chainId']}: {c['name']}" for c in matches]
        raise ValueError(
            f"Found {len(matches)} chains matching '{identifier}'. Please use chainId:\n"
            + "\n".join(names)
        )
    return matches[0]


def extract_free_rpcs(chain: dict) -> list:
    """Get list of free HTTPS RPCs (no API key required) from chain object."""
    rpcs = []
    for rpc in chain.get("rpc", []):
        url = rpc.get("url", "") if isinstance(rpc, dict) else rpc
        # Only take HTTPS, skip URLs with placeholder keys like ${...}
        if url.startswith("https://") and "${" not in url:
            rpcs.append(url)
    return rpcs


def infer_env_var(chain_name: str) -> str:
    """
    Auto-infer environment variable name from chain name.
    e.g.: "BNB Smart Chain Mainnet" → "BNB_RPCS"
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
        help="Chain ID (number) or chain name (substring). e.g.: 56, 1, 137, 'BNB Smart Chain'"
    )
    parser.add_argument(
        "--timeout", type=int, default=10,
        help="Timeout per request in seconds (default: 10)"
    )
    parser.add_argument(
        "--workers", type=int, default=10,
        help="Number of parallel check threads (default: 10)"
    )
    parser.add_argument(
        "--env-var", dest="env_var", default=None,
        help="Environment variable name to print (default: auto-inferred from chain name)"
    )
    args = parser.parse_args()

    # Get chain info
    try:
        chains = fetch_chainlist()
        chain = find_chain(chains, args.chain)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    chain_name = chain["name"]
    chain_id = chain["chainId"]
    rpc_list = extract_free_rpcs(chain)
    env_var = args.env_var or infer_env_var(chain_name)

    print(f"Chain: {chain_name} (chainId={chain_id})")
    print(f"Found {len(rpc_list)} free HTTPS RPCs")
    print(f"Environment variable: {env_var}")
    print(f"Timeout: {args.timeout}s | Workers: {args.workers}")
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
            status = "PASS" if ok else "FAIL"
            print(f"{status} | {url}")
            if not ok:
                print(f"       Reason: {reason}")
            if ok:
                passed.append(url)
            else:
                failed.append((url, reason))

    print("\n" + "=" * 70)
    print(f"\nResults: {len(passed)} PASS / {len(failed)} FAIL / {len(rpc_list)} total\n")

    if not passed:
        print("Warning: No RPCs passed!", file=sys.stderr)
        sys.exit(1)

    print("RPCs that passed:")
    for url in passed:
        print(f"   {url}")
    print()
    print(f"# Add the following line to chainslake-run/.env:")
    print(f"{env_var}=" + ",".join(passed))


if __name__ == "__main__":
    main()
