# ethereum.transactions

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | 2026-07-12 15:49:26 |
| Ngày update gần nhất | 2026-07-13 00:14:39 |
| Số bản ghi | 279620 |
| Số file | 6 |
| Dung lượng | 91.2 MB |
| frequentType | block |
| fromBlock | 25516917 |
| toBlock | 25517819 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum_origin.transaction_blocks, ethereum_origin.blocks_receipt
- **Downstream tables**: ethereum_token.erc20_transfer

## Schema

| Column | Type | Example |
|---|---|---|
| block_date | date | `2026-07-12T00:00:00Z` |
| block_number | bigint | `25517064` |
| block_time | timestamp | `2026-07-12T14:13:35Z` |
| hash | string | `0x350ea0c4edb29d75c68a6d3aaf9312e8ad6baaee85c7babb183d7c3886261545` |
| updated_time | timestamp | `2026-07-13T00:14:37.182Z` |
| access_list | string | `NULL` |
| block_hash | string | `0x2050232e49b335ba3dd27a1a46fde19e08dcefe732a44123e5a7999df4450eba` |
| method_id | string | `0xa0000000` |
| data | string | `0xa0000000000000000000000000000000cfecc1c9f3cb6190cb1ff7f65a130bfbe5107d38000...` |
| from | string | `0x5934e06498db785ff26807161ce9d09063231321` |
| gas_limit | decimal(38,0) | `246674` |
| gas_price | decimal(38,0) | `138362111893` |
| gas_used | decimal(38,0) | `205819` |
| index | decimal(38,0) | `0` |
| max_fee_per_gas | decimal(38,0) | `NULL` |
| max_priority_fee_per_gas | decimal(38,0) | `NULL` |
| nonce | decimal(38,0) | `110689` |
| priority_fee_per_gas | decimal(38,0) | `NULL` |
| success | boolean | `True` |
| to | string | `0xbdb3ba9ffe392549e1f8658dd2630c141fdf47b6` |
| type | string | `0x2` |
| value | decimal(38,18) | `25517064.0` |
