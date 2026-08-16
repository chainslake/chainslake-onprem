# ethereum_origin.blocks_receipt

## Status

| Attribute | Value |
|---|---|
| Created At | 2026-07-12 15:11:49 |
| Last Updated At | 2026-07-18 08:33:28 |
| Record Count | 1505 |
| File Count | 12 |
| Size | 235.6 MB |
| frequentType | block |
| fromBlock | 25516616 |
| toBlock | 25518120 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum_origin.transaction_blocks
- **Downstream tables**: ethereum.blocks, ethereum.logs, ethereum.transactions

## Schema

| Column | Type | Example |
|---|---|---|
| block_date | date | `2026-07-12T00:00:00Z` |
| block_number | bigint | `25517685` |
| block_time | timestamp | `2026-07-12T16:18:23Z` |
| updated_time | timestamp | `2026-07-13T00:11:46.651Z` |
| block_receipt | string | `[{"blockHash":"0xaf52563eabb494bde6f7a088711e7f2782b1c7fc36823827206d4a545ffb...` |
| number_tx | int | `408` |
| number_logs | int | `704` |
