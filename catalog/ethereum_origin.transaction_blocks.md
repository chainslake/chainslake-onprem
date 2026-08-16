# ethereum_origin.transaction_blocks

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | 2026-07-12 15:45:00 |
| Ngày update gần nhất | 2026-07-26 17:01:26 |
| Số bản ghi | 2107 |
| Số file | 14 |
| Dung lượng | 324.9 MB |
| frequentType | block |
| fromBlock | 25516315 |
| toBlock | 25518421 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: _RPC Node (Blockchain)_
- **Downstream tables**: ethereum.blocks, ethereum.transactions, ethereum_origin.blocks_receipt

## Schema

| Column | Type | Index | Partition | Example |
|---|---|---|---|---|
| block_date | date | 1 | x | `2026-07-12T00:00:00Z` |
| block_number | bigint | 2 |  | `25517821` |
| block_time | timestamp | 3 |  | `2026-07-12T16:45:35Z` |
| updated_time | timestamp |  |  | `2026-07-18T08:20:03.717Z` |
| transactions | string |  |  | `{"number":"0x1855efd","hash":"0x43c5a6e2c72b9ae33cb94a5c6d0ba0ba8008fd967f4da...` |
| number_tx | int |  |  | `276` |
