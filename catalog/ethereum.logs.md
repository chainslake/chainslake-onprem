# ethereum.logs

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | 2026-07-12 15:49:25 |
| Ngày update gần nhất | 2026-07-13 00:14:38 |
| Số bản ghi | 754127 |
| Số file | 6 |
| Dung lượng | 64.3 MB |
| frequentType | block |
| fromBlock | 25516917 |
| toBlock | 25517819 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum_origin.blocks_receipt
- **Downstream tables**: ethereum_decoded.erc20_evt_transfer

## Schema

| Column | Type | Example |
|---|---|---|
| block_date | date | `2026-07-12T00:00:00Z` |
| block_time | timestamp | `2026-07-12T13:57:11Z` |
| block_number | bigint | `25516982` |
| updated_time | timestamp | `2026-07-13T00:14:35.259Z` |
| block_hash | string | `0xc0402cccc8ef326f055fd1fed4434c3bf4af1664cddd1c4873c46605275ad30d` |
| contract_address | string | `0xd1d2eb1b1e90b638588728b4130137d262c87cae` |
| topic1 | string | `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` |
| topic2 | string | `0x000000000000000000000000187c9fbf5bd0f266883c03f320260c407c7b4100` |
| topic3 | string | `0x000000000000000000000000bb26df665c594c723b746f68010d4dedbd441c8c` |
| topic4 | string | `NULL` |
| data | string | `0x0000000000000000000000000000000000000000000000000000452b312d3252` |
| tx_hash | string | `0x09adbc405b3808eba822c31799df13e985e051ca0c65cf07e6cf5122c02960f0` |
| index | int | `0` |
| tx_index | int | `0` |
