"""
Script to call the 4 JSON-RPC methods used by check_rpcs.py on an EVM chain,
using the RPC list from chainslake-run/.env.

Purpose:
  - Read the RPC list for a chain from chainslake-run/.env
      * <CHAIN>_RPCS                    for eth_blockNumber / eth_getBlockByNumber / eth_getBlockReceipts
      * <CHAIN>_TRACE_BLOCK_RPCS        for trace_block (switched automatically)
  - Send the JSON-RPC request to each RPC in order until one returns a result
  - Print the raw JSON result returned by the RPC

Supported methods (same as check_rpcs.py):
  - eth_blockNumber        No params needed
  - eth_getBlockByNumber   [block_hex, full_transactions]  (full_transactions defaults to true)
  - eth_getBlockReceipts   [block_hex]
  - trace_block            [block_hex]  (uses <CHAIN>_TRACE_BLOCK_RPCS automatically)

Input (CLI positional arguments):
  1. chain_name   Chain name used to look up the env var in chainslake-run/.env
                  (e.g. `ethereum` -> ETHEREUM_RPCS). Case-insensitive.
  2. method_name  One of: eth_blockNumber, eth_getBlockByNumber, eth_getBlockReceipts, trace_block
  3. block_number Block number (required except for eth_blockNumber). Auto-converted to hex.

Options:
  --param <json>  JSON array of extra params appended AFTER the block number.
                  For eth_getBlockByNumber the second param (full transactions)
                  defaults to true, matching check_rpcs.py; pass --param '[false]'
                  to get transaction hashes only. When no block_number is given,
                  --param is used as the whole param list.
  --env-var       Environment variable name to read directly, bypassing the
                  chain-name -> variable-name inference (e.g. --env-var ETHEREUM_RPCS).
                  When set explicitly, it is used as-is (no auto TRACE_BLOCK switching).
  --env-file      Path to the .env file (default: chainslake-run/.env relative to repo root)
  --timeout       Timeout per request in seconds (default: 10)

RPC list selection (automatic):
  - trace_block        -> <CHAIN>_TRACE_BLOCK_RPCS  (falls back to <CHAIN>_RPCS with a warning if empty)
  - other 3 methods    -> <CHAIN>_RPCS

Output:
  The raw JSON result of the first RPC that returns a result, printed in a
  readable JSON format. Exit code 0 on success, 1 on failure.

Examples:
  python script/get_from_rpc.py ethereum eth_blockNumber
  python script/get_from_rpc.py ethereum eth_getBlockByNumber 12345
  python script/get_from_rpc.py ethereum eth_getBlockByNumber 12345 --param '[false]'
  python script/get_from_rpc.py ethereum eth_getBlockReceipts 12345
  python script/get_from_rpc.py ethereum trace_block 12345
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# Methods supported by this tool (same set as check_rpcs.py)
SUPPORTED_METHODS = [
    "eth_blockNumber",
    "eth_getBlockByNumber",
    "eth_getBlockReceipts",
    "trace_block",
]

# Methods that take the block number as their first param
BLOCK_METHODS = [
    "eth_getBlockByNumber",
    "eth_getBlockReceipts",
    "trace_block",
]


# ─── .env parsing ─────────────────────────────────────────────────────────────


def find_env_file(default: str) -> str:
    """Locate the .env file. Prefer --env-file, else default under repo root."""
    if os.path.isfile(default):
        return default
    # Fall back to repo root: chainslake-run/.env
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate = os.path.join(repo_root, default)
    if os.path.isfile(candidate):
        return candidate
    return default


def load_env(path: str) -> dict:
    """Parse a simple KEY=VALUE .env file into a dict."""
    env = {}
    if not os.path.isfile(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def infer_env_var(chain_name: str) -> str:
    """Infer the RPC env var name from a chain name. e.g. ethereum -> ETHEREUM_RPCS."""
    first_word = chain_name.strip().split()[0].upper()
    first_word = "".join(c for c in first_word if c.isalnum())
    return f"{first_word}_RPCS"


def split_rpcs(value: str) -> list:
    """Split a comma-separated RPC string into a list of non-empty URLs."""
    return [u.strip() for u in value.split(",") if u.strip()]


# ─── JSON-RPC call ────────────────────────────────────────────────────────────


def rpc_call(url: str, method: str, params: list, timeout: int) -> dict:
    """Call a JSON-RPC endpoint and return the full response dict."""
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


def to_hex_block(number) -> str:
    """Convert a block number (int or hex string) to hex form like '0x...'."""
    if isinstance(number, int):
        return hex(number)
    s = str(number)
    if s.lower().startswith("0x"):
        return s
    try:
        return hex(int(s))
    except ValueError:
        raise ValueError(f"Invalid block number: {number}")


# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Call one of the 4 check_rpcs.py JSON-RPC methods on an EVM chain using RPCs from chainslake-run/.env"
    )
    parser.add_argument("chain_name", help="Chain name, e.g. ethereum, bnb, polygon")
    parser.add_argument(
        "method_name",
        help=f"One of: {', '.join(SUPPORTED_METHODS)}"
    )
    parser.add_argument(
        "block_number", nargs="?", default=None,
        help="Block number (auto-converted to hex). Required except for eth_blockNumber."
    )
    parser.add_argument(
        "--param", default=None,
        help="JSON array of extra params appended AFTER the block number "
             "(e.g. --param '[false]' for eth_getBlockByNumber). "
             "When no block_number is given, --param is the whole param list."
    )
    parser.add_argument(
        "--env-var", dest="env_var", default=None,
        help="Environment variable name to read directly (e.g. ETHEREUM_RPCS)"
    )
    parser.add_argument(
        "--env-file", default="chainslake-run/.env",
        help="Path to the .env file (default: chainslake-run/.env)"
    )
    parser.add_argument("--timeout", type=int, default=10, help="Timeout per request (seconds)")
    args = parser.parse_args()

    # Validate method
    if args.method_name not in SUPPORTED_METHODS:
        print(
            f"Error: unsupported method '{args.method_name}'. Supported methods: "
            + ", ".join(SUPPORTED_METHODS),
            file=sys.stderr
        )
        sys.exit(1)

    env = load_env(find_env_file(args.env_file))

    # Resolve the RPC env var name.
    # trace_block automatically uses <CHAIN>_TRACE_BLOCK_RPCS unless --env-var is given.
    if args.env_var:
        env_var = args.env_var
    elif args.method_name == "trace_block":
        env_var = infer_env_var(args.chain_name).replace("_RPCS", "_TRACE_BLOCK_RPCS")
    else:
        env_var = infer_env_var(args.chain_name)

    rpcs = split_rpcs(env.get(env_var, ""))
    sources = [f"{env_var} ({len(rpcs)} RPCs)"]

    # Fallback for trace_block if the trace list is empty/missing
    if args.method_name == "trace_block" and not rpcs:
        fallback_var = env_var.replace("_TRACE_BLOCK_RPCS", "_RPCS")
        print(
            f"Warning: {env_var} is empty/missing; falling back to {fallback_var}",
            file=sys.stderr
        )
        rpcs = split_rpcs(env.get(fallback_var, ""))
        sources.append(f"{fallback_var} ({len(rpcs)} RPCs)")

    if not rpcs:
        print(
            f"Error: no RPCs found for '{args.chain_name}' (env var {env_var} empty or missing "
            f"in {args.env_file}).",
            file=sys.stderr
        )
        print(
            f"Hint: use --env-var to specify the variable, or add {env_var}=<rpc1,rpc2,...> "
            f"to {args.env_file}.",
            file=sys.stderr
        )
        sys.exit(1)

    # Parse extra params from --param
    extra = []
    if args.param is not None:
        try:
            extra = json.loads(args.param)
        except json.JSONDecodeError:
            print(f"Error: --param is not valid JSON: {args.param}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(extra, list):
            print("Error: --param must be a JSON array", file=sys.stderr)
            sys.exit(1)

    # Build request params according to the method
    if args.method_name == "eth_blockNumber":
        params = extra
    else:
        if args.block_number is None:
            print(
                f"Error: method '{args.method_name}' requires a block_number (3rd argument).",
                file=sys.stderr
            )
            sys.exit(1)
        try:
            block_hex = to_hex_block(args.block_number)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if args.method_name == "eth_getBlockByNumber" and not extra:
            # Default to full transaction objects, matching check_rpcs.py
            params = [block_hex, True]
        else:
            params = [block_hex] + extra

    print(f"Chain: {args.chain_name} | RPC vars: {', '.join(sources)}")
    print(f"Method: {args.method_name} | Params: {json.dumps(params)}")
    print("=" * 70)

    errors = []
    for url in rpcs:
        try:
            resp = rpc_call(url, args.method_name, params, args.timeout)
        except urllib.error.HTTPError as e:
            errors.append(f"{url} -> HTTPError {e.code} {e.reason}")
            print(f"FAIL | {url} | HTTP {e.code}")
            continue
        except urllib.error.URLError as e:
            errors.append(f"{url} -> URLError {e.reason}")
            print(f"FAIL | {url} | URLError {e.reason}")
            continue
        except TimeoutError:
            errors.append(f"{url} -> Timeout")
            print(f"FAIL | {url} | Timeout")
            continue
        except Exception as e:
            errors.append(f"{url} -> {type(e).__name__}: {e}")
            print(f"FAIL | {url} | {type(e).__name__}: {e}")
            continue

        # Inspect the response
        if "error" in resp:
            errors.append(f"{url} -> RPC error {resp['error']}")
            print(f"FAIL | {url} | RPC error: {json.dumps(resp['error'])}")
            continue
        if "result" not in resp:
            errors.append(f"{url} -> response missing 'result'")
            print(f"FAIL | {url} | response missing 'result'")
            continue

        # Success
        print(f"OK   | {url}")
        print("-" * 70)
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        sys.exit(0)

    # All RPCs failed
    print("\n" + "=" * 70)
    print("Error: all RPCs failed:", file=sys.stderr)
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()