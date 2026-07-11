"""
Script kiểm tra danh sách RPC cho bất kỳ EVM chain nào.

Mục đích:
  - Tự động lấy danh sách RPC từ chainlist.org theo chain_id hoặc tên chain
  - Kiểm tra từng RPC có đáp ứng 3 yêu cầu sau không:
      1. eth_blockNumber — trả về latest block number
      2. eth_getBlockByNumber — trả về block data đầy đủ (có transactions)
      3. eth_getBlockReceipts — trả về receipts của block (bao gồm logs)
  - In ra danh sách PASS/FAIL và chuỗi <ENV_VAR>=<rpc1,rpc2,...> để dán vào .env

Input (argument dòng lệnh):
  - chain_id (int): chain ID theo EIP-155, ví dụ 56 (BNB), 1 (Ethereum), 137 (Polygon)
  - Hoặc tên chain (str): substring khớp với tên chain trong chainlist.org, ví dụ "BNB Smart Chain"

Options:
  --timeout   Timeout mỗi request (giây), mặc định 10
  --workers   Số luồng song song, mặc định 10
  --env-var   Tên biến môi trường để in ra, mặc định tự suy ra từ tên chain
              Ví dụ: --env-var BNB_RPCS

Output:
  - PASS/FAIL cho từng RPC
  - Tổng kết số lượng
  - Dòng <ENV_VAR>=... để copy vào .env

Ví dụ:
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
    """Gọi JSON-RPC endpoint và trả về response dict."""
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
    Kiểm tra object có đủ các field yêu cầu không.
    Trả về (ok: bool, missing: list)
    """
    if not isinstance(obj, dict):
        return False, fields
    missing = [f for f in fields if f not in obj]
    return len(missing) == 0, missing


def check_rpc(url: str, timeout: int) -> tuple:
    """
    Kiểm tra một RPC URL theo 3 bước.
    Trả về (url, passed: bool, reason: str)
    """
    try:
        # Bước 1: eth_blockNumber
        resp = rpc_call(url, "eth_blockNumber", [], timeout)
        block_hex = resp.get("result")
        if not block_hex or not isinstance(block_hex, str):
            return url, False, "eth_blockNumber: kết quả không hợp lệ"

        # Bước 2: eth_getBlockByNumber
        resp2 = rpc_call(url, "eth_getBlockByNumber", [block_hex, True], timeout)
        block = resp2.get("result")
        required_block_fields = [
            "number", "hash", "parentHash", "nonce", "sha3Uncles",
            "logsBloom", "transactionsRoot", "stateRoot", "miner",
            "difficulty", "extraData", "size",
            "gasLimit", "gasUsed", "timestamp", "transactions"
        ]
        ok, missing = has_fields(block, required_block_fields)
        if not ok:
            return url, False, f"eth_getBlockByNumber: thiếu fields {missing}"

        # Kiểm tra transactions array (nếu block có tx thì check field của tx)
        txs = block.get("transactions", [])
        if isinstance(txs, list) and len(txs) > 0:
            required_tx_fields = [
                "hash", "nonce", "blockHash", "blockNumber", "transactionIndex",
                "from", "to", "value", "gasPrice", "gas", "input", "r", "s", "type"
            ]
            ok, missing = has_fields(txs[0], required_tx_fields)
            if not ok:
                return url, False, f"transaction object thiếu fields {missing}"

        # Bước 3: eth_getBlockReceipts
        resp3 = rpc_call(url, "eth_getBlockReceipts", [block_hex], timeout)
        receipts = resp3.get("result")
        if receipts is None:
            return url, False, "eth_getBlockReceipts: result=null (không hỗ trợ)"
        if not isinstance(receipts, list):
            return url, False, f"eth_getBlockReceipts: result không phải array, got {type(receipts).__name__}"

        # Kiểm tra fields của receipt (nếu block có receipt)
        if len(receipts) > 0:
            required_receipt_fields = [
                "blockHash", "blockNumber", "contractAddress", "cumulativeGasUsed",
                "effectiveGasPrice", "from", "gasUsed", "to", "status",
                "transactionHash", "transactionIndex", "type", "logsBloom", "logs"
            ]
            ok, missing = has_fields(receipts[0], required_receipt_fields)
            if not ok:
                return url, False, f"receipt object thiếu fields {missing}"

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
    Tải danh sách chains từ chainlist.org/rpcs.json.
    Dùng curl thay urllib vì chainlist.org block user-agent mặc định của Python.
    """
    print("📡 Đang tải danh sách chain từ chainlist.org...")
    result = subprocess.run(
        ["curl", "-s", "--max-time", "30", CHAINLIST_URL],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl thất bại (exit {result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout)


def find_chain(chains: list, identifier: str) -> dict:
    """
    Tìm chain theo chain_id (số) hoặc tên (chuỗi substring, case-insensitive).
    Ném ValueError nếu không tìm thấy hoặc tìm thấy nhiều hơn 1 kết quả.
    """
    # Thử parse thành số nguyên (chain ID)
    try:
        chain_id = int(identifier)
        matches = [c for c in chains if c.get("chainId") == chain_id]
        if not matches:
            raise ValueError(f"Không tìm thấy chain với chainId={chain_id}")
        return matches[0]
    except ValueError as e:
        # Nếu lỗi từ chính ta raise thì re-raise
        if "Không tìm thấy" in str(e):
            raise

    # Tìm theo tên (substring, case-insensitive)
    name_lower = identifier.lower()
    matches = [c for c in chains if name_lower in c.get("name", "").lower()]
    if not matches:
        raise ValueError(f"Không tìm thấy chain với tên chứa '{identifier}'")
    if len(matches) > 1:
        names = [f"  chainId={c['chainId']}: {c['name']}" for c in matches]
        raise ValueError(
            f"Tìm thấy {len(matches)} chain khớp với '{identifier}'. Hãy dùng chainId:\n"
            + "\n".join(names)
        )
    return matches[0]


def extract_free_rpcs(chain: dict) -> list:
    """Lấy danh sách RPC HTTPS free (không cần API key) từ chain object."""
    rpcs = []
    for rpc in chain.get("rpc", []):
        url = rpc.get("url", "") if isinstance(rpc, dict) else rpc
        # Chỉ lấy HTTPS, bỏ qua các URL có placeholder key dạng ${...}
        if url.startswith("https://") and "${" not in url:
            rpcs.append(url)
    return rpcs


def infer_env_var(chain_name: str) -> str:
    """
    Tự suy ra tên biến môi trường từ tên chain.
    Ví dụ: "BNB Smart Chain Mainnet" → "BNB_RPCS"
           "Ethereum Mainnet"        → "ETHEREUM_RPCS"
           "Polygon Mainnet"         → "POLYGON_RPCS"
    """
    first_word = chain_name.strip().split()[0].upper()
    # Loại bỏ ký tự đặc biệt
    first_word = "".join(c for c in first_word if c.isalnum())
    return f"{first_word}_RPCS"


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Kiểm tra RPC endpoints của một EVM chain từ chainlist.org"
    )
    parser.add_argument(
        "chain",
        help="Chain ID (số) hoặc tên chain (substring). Ví dụ: 56, 1, 137, 'BNB Smart Chain'"
    )
    parser.add_argument(
        "--timeout", type=int, default=10,
        help="Timeout mỗi request tính bằng giây (mặc định: 10)"
    )
    parser.add_argument(
        "--workers", type=int, default=10,
        help="Số luồng kiểm tra song song (mặc định: 10)"
    )
    parser.add_argument(
        "--env-var", dest="env_var", default=None,
        help="Tên biến môi trường để in ra (mặc định: tự suy từ tên chain)"
    )
    args = parser.parse_args()

    # Lấy thông tin chain
    try:
        chains = fetch_chainlist()
        chain = find_chain(chains, args.chain)
    except ValueError as e:
        print(f"❌ Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    chain_name = chain["name"]
    chain_id = chain["chainId"]
    rpc_list = extract_free_rpcs(chain)
    env_var = args.env_var or infer_env_var(chain_name)

    print(f"🔗 Chain: {chain_name} (chainId={chain_id})")
    print(f"📋 Tìm thấy {len(rpc_list)} RPC HTTPS free")
    print(f"🔑 Biến môi trường: {env_var}")
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
                print(f"       Lý do: {reason}")
            if ok:
                passed.append(url)
            else:
                failed.append((url, reason))

    print("\n" + "=" * 70)
    print(f"\n📊 Kết quả: {len(passed)} PASS / {len(failed)} FAIL / {len(rpc_list)} total\n")

    if not passed:
        print("⚠️  Không có RPC nào pass!", file=sys.stderr)
        sys.exit(1)

    print("✅ RPC đạt yêu cầu:")
    for url in passed:
        print(f"   {url}")
    print()
    print(f"# Thêm dòng sau vào chainslake-run/.env:")
    print(f"{env_var}=" + ",".join(passed))


if __name__ == "__main__":
    main()
