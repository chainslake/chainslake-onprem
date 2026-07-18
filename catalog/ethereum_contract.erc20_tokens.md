# ethereum_contract.erc20_tokens

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | 2026-07-12 15:49:59 |
| Ngày update gần nhất | 2026-07-13 00:18:13 |
| Số bản ghi | 2793 |
| Số file | 30 |
| Dung lượng | 227.7 KB |
| frequentType | block |
| fromBlock | 25516917 |
| toBlock | 25517819 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum_decoded.erc20_evt_transfer
- **Downstream tables**: ethereum_token.erc20_transfer

## Schema

| Column | Type | Example |
|---|---|---|
| contract_address | string | `0xc71c923445abdfc2c9b50292d8498745330f18ab` |
| updated_time | timestamp | `2026-07-13T00:16:28.291Z` |
| name | string | `SY YieldFi vyUSD` |
| symbol | string | `SY-vyUSD` |
| decimals | int | `18` |

## SQL Transform

```sql


with list_contract_address as (
    select distinct contract_address
    from ${list_input_tables}
    where block_number >= ${from} and block_number <= ${to}
)

${if table_existed}

, new_contract_address as (
    select new.contract_address from list_contract_address new
    left join ${output_table} old
    on new.contract_address = old.contract_address
    where old.name is null
)

, new_contract_address_repartition as (
    select /*+ REPARTITION(10) */ contract_address from new_contract_address
)

${else}

, new_contract_address_repartition as (
    select /*+ REPARTITION(10) */ contract_address from list_contract_address
)

${endif}

select contract_address
, current_timestamp() as updated_time
, erc20(CONCAT(contract_address, ' name')) as name
, erc20(CONCAT(contract_address, ' symbol')) as symbol
, cast(erc20(CONCAT(contract_address, ' decimals')) as INT) as decimals
from new_contract_address_repartition

```

## ABI

### erc20

#### `name() returns (string)` — view function

```json
{
  "constant": true,
  "inputs": [],
  "name": "name",
  "outputs": [
    {
      "name": "",
      "type": "string"
    }
  ],
  "payable": false,
  "stateMutability": "view",
  "type": "function"
}
```

#### `symbol() returns (string)` — view function

```json
{
  "constant": true,
  "inputs": [],
  "name": "symbol",
  "outputs": [
    {
      "name": "",
      "type": "string"
    }
  ],
  "payable": false,
  "stateMutability": "view",
  "type": "function"
}
```

#### `decimals() returns (uint256)` — view function

```json
{
  "constant": true,
  "inputs": [],
  "name": "decimals",
  "outputs": [
    {
      "name": "",
      "type": "uint256"
    }
  ],
  "payable": false,
  "stateMutability": "view",
  "type": "function"
}
```

#### `totalSupply() returns (uint256)` — view function

```json
{
  "constant": true,
  "inputs": [],
  "name": "totalSupply",
  "outputs": [
    {
      "name": "",
      "type": "uint256"
    }
  ],
  "payable": false,
  "stateMutability": "view",
  "type": "function"
}
```

#### `balanceOf(address _owner) returns (uint256)` — view function

```json
{
  "constant": true,
  "inputs": [
    {
      "name": "_owner",
      "type": "address"
    }
  ],
  "name": "balanceOf",
  "outputs": [
    {
      "name": "",
      "type": "uint256"
    }
  ],
  "payable": false,
  "stateMutability": "view",
  "type": "function"
}
```

