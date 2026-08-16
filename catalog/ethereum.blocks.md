# ethereum.blocks

## Status

| Attribute | Value |
|---|---|
| Created At | 2026-07-12 15:49:26 |
| Last Updated At | 2026-07-13 00:14:31 |
| Record Count | 903 |
| File Count | 3 |
| Size | 21.3 KB |
| frequentType | block |
| fromBlock | 25516917 |
| toBlock | 25517819 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum_origin.transaction_blocks, ethereum_origin.blocks_receipt
- **Downstream tables**: _None_

## Schema

| Column | Type | Example |
|---|---|---|
| block_date | date | `2026-07-12T00:00:00Z` |
| block_number | bigint | `25517791` |
| block_time | timestamp | `2026-07-12T16:39:35Z` |
| number_tx | int | `99` |
| number_logs | int | `256` |

## SQL Transform

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
