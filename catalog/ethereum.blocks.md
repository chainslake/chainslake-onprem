# ethereum.blocks

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | 2026-07-12 15:49:26 |
| Ngày update gần nhất | 2026-08-08 16:45:20 |
| Số bản ghi | 2107 |
| Số file | 7 |
| Dung lượng | 49.4 KB |
| frequentType | block |
| fromBlock | 25516315 |
| toBlock | 25518421 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum_origin.transaction_blocks, ethereum_origin.blocks_receipt
- **Downstream tables**: _None_

## Schema

| Column | Type | Index | Partition | Example |
|---|---|---|---|---|
| block_date | date | 1 | x | `2026-07-12T00:00:00Z` |
| block_number | bigint | 2 |  | `25517791` |
| block_time | timestamp | 3 |  | `2026-07-12T16:39:35Z` |
| number_tx | int |  |  | `99` |
| number_logs | int |  |  | `256` |

## SQL Transform

### Header

| Key | Value |
|---|---|
| frequent_type | `block` |
| list_input_tables | `ethereum_origin.transaction_blocks,ethereum_origin.blocks_receipt` |
| transaction_blocks | `ethereum_origin.transaction_blocks` |
| blocks_receipt | `ethereum_origin.blocks_receipt` |
| output_table | `ethereum.blocks` |
| re_partition_by_range | `block_date,block_number` |
| partition_by | `block_date` |
| write_mode | `Append` |
| number_index_columns | `3` |

### SQL Body

```sql


with transaction_blocks as (
    select block_date, block_number, block_time, number_tx
    from ${transaction_blocks}
    where block_number >= ${from} and block_number <= ${to}
)
, blocks_receipt as (
    select block_date, block_number, block_time, number_logs
    from ${blocks_receipt}
    where block_number >= ${from} and block_number <= ${to}
)

select t.block_date
    , t.block_number
    , t.block_time
    , t.number_tx
    , l.number_logs
from transaction_blocks t
inner join blocks_receipt l
on t.block_number = l.block_number

```
