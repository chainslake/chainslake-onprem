# ethereum_origin.blocks_receipt

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | 2026-07-12 15:11:49 |
| Ngày update gần nhất | 2026-07-26 17:04:30 |
| Số bản ghi | 2107 |
| Số file | 16 |
| Dung lượng | 321.5 MB |
| frequentType | block |
| fromBlock | 25516315 |
| toBlock | 25518421 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum_origin.transaction_blocks
- **Downstream tables**: ethereum.blocks, ethereum.logs, ethereum.transactions

## Schema

| Column | Type | Index | Partition | Example |
|---|---|---|---|---|
| block_date | date | 1 | x | `2026-07-12T00:00:00Z` |
| block_number | bigint | 2 |  | `25518121` |
| block_time | timestamp | 3 |  | `2026-07-12T17:46:11Z` |
| updated_time | timestamp |  |  | `2026-07-26T17:01:41.654Z` |
| block_receipt | string |  |  | `[{"blockHash":"0xb17860d415c975f28634ee394aeadfdd251d288f203cf2159d80c4e1e663...` |
| number_tx | int |  |  | `203` |
| number_logs | int |  |  | `653` |
