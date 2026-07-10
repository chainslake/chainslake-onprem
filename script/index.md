# Script Index

Thư mục này chứa các Python script do Agent tự viết để phục vụ các tác vụ lặp lại hoặc cần tool đặc biệt.

> **Hướng dẫn cho Agent**: Trước khi viết script mới, kiểm tra index này để tránh trùng lặp. Sau khi viết script mới, cập nhật index này ngay lập tức.

---

## check_rpcs.py
- **Mục đích**: Kiểm tra danh sách RPC của bất kỳ EVM chain nào từ chainlist.org. Xác nhận từng RPC có hỗ trợ đầy đủ 3 API cần thiết (eth_blockNumber, eth_getBlockByNumber, eth_getBlockReceipts) và in ra chuỗi `<ENV_VAR>=...` để dán vào `.env`.
- **Input**:
  - Positional: `chain` — chain ID (số, ví dụ `56`) hoặc tên chain (substring, ví dụ `"BNB Smart Chain Mainnet"`)
  - `--timeout` — timeout mỗi request (giây, mặc định 10)
  - `--workers` — số luồng song song (mặc định 10)
  - `--env-var` — tên biến môi trường output (mặc định: tự suy từ tên chain, ví dụ `BNB_RPCS`)
- **Output**: PASS/FAIL từng RPC + dòng `<ENV_VAR>=<rpc1,rpc2,...>` để copy vào `chainslake-run/.env`
- **Ví dụ**:
  - `python script/check_rpcs.py 56`
  - `python script/check_rpcs.py 1 --env-var ETHEREUM_RPCS`
  - `python script/check_rpcs.py 137 --timeout 15 --workers 20`
