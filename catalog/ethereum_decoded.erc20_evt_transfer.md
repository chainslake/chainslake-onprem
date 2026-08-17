# ethereum_decoded.erc20_evt_transfer

## Status

| Property | Value |
|---|---|
| Created date | 2026-07-12 15:49:46 |
| Last updated | 2026-07-26 16:47:13 |
| Row count | 721252 |
| File count | 10 |
| Size | 50.1 MB |
| frequentType | block |
| fromBlock | 25516616 |
| toBlock | 25518120 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum.logs
- **Downstream tables**: ethereum_contract.erc20_tokens, ethereum_token.erc20_transfer

## Schema

| Column | Type | Index | Partition | Example |
|---|---|---|---|---|
| block_date | date | 1 | x | `2026-07-12T00:00:00Z` |
| block_number | bigint | 2 |  | `25516767` |
| block_time | timestamp | 3 |  | `2026-07-12T13:13:47Z` |
| updated_time | timestamp |  |  | `2026-07-26T16:47:11.513Z` |
| contract_address | string |  |  | `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` |
| tx_hash | string |  |  | `0x92020ba2cb61bb25b0f4545a2c1c9c6850d3ff0eaf1c1a78ba56b1b63bab2584` |
| evt_index | int |  |  | `0` |
| from | string |  |  | `0xbdb3ba9ffe392549e1f8658dd2630c141fdf47b6` |
| to | string |  |  | `0xf4acdac048c14c5e49bbede0c72444d806a75cde` |
| value | string |  |  | `253584336975104662` |

## SQL Transform

### Header

| Key | Value |
|---|---|
| frequent_type | `block` |
| list_input_tables | `ethereum.logs` |
| logs_table_name | `ethereum.logs` |
| pre_decode_tables | `erc20_evt_transfer` |
| output_table | `ethereum_decoded.erc20_evt_transfer` |
| re_partition_by_range | `block_date,block_time` |
| partition_by | `block_date` |
| write_mode | `Append` |
| number_index_columns | `3` |

### SQL Body

```sql


select * from ${pre_decode_tables}
```

## ABI

### erc20

#### `Transfer(indexed address from, indexed address to, uint256 value)` — event

```json
{
  "anonymous": false,
  "inputs": [
    {
      "indexed": true,
      "name": "from",
      "type": "address"
    },
    {
      "indexed": true,
      "name": "to",
      "type": "address"
    },
    {
      "indexed": false,
      "name": "value",
      "type": "uint256"
    }
  ],
  "name": "Transfer",
  "type": "event"
}
```