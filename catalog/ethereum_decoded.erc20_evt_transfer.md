# ethereum_decoded.erc20_evt_transfer

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | 2026-07-12 15:49:46 |
| Ngày update gần nhất | 2026-07-13 00:14:59 |
| Số bản ghi | 463035 |
| Số file | 6 |
| Dung lượng | 33.3 MB |
| frequentType | block |
| fromBlock | 25516917 |
| toBlock | 25517819 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum.logs
- **Downstream tables**: ethereum_contract.erc20_tokens, ethereum_token.erc20_transfer

## Schema

| Column | Type | Example |
|---|---|---|
| block_date | date | `2026-07-12T00:00:00Z` |
| block_number | bigint | `25517066` |
| block_time | timestamp | `2026-07-12T14:13:59Z` |
| updated_time | timestamp | `2026-07-13T00:14:55.864Z` |
| contract_address | string | `0xb5ffa377ec90ba776d9aa4c63dfc983d9937eb8b` |
| tx_hash | string | `0xdf34427b07cf46ae1b31d1d2797ea472bdaa61480fde30c7461d7053da30c1e9` |
| evt_index | int | `2` |
| from | string | `0xb5ffa377ec90ba776d9aa4c63dfc983d9937eb8b` |
| to | string | `0x0e36de8d9f51cb7a18e0187e96e70bea54131527` |
| value | string | `4200000000000000000` |

## SQL Transform

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

