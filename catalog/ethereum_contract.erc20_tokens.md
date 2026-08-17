# ethereum_contract.erc20_tokens

## Status

| Property | Value |
|---|---|
| Created date | 2026-07-26 16:54:25 |
| Last updated | 2026-07-26 16:58:18 |
| Row count | 1457 |
| File count | 10 |
| Size | 106.0 KB |
| frequentType | block |
| fromBlock | 25517820 |
| toBlock | 25518120 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum_decoded.erc20_evt_transfer
- **Downstream tables**: ethereum_token.erc20_transfer

## Schema

| Column | Type | Index | Partition | Example |
|---|---|---|---|---|
| contract_address | string | 1 |  | `0x8f8221afbb33998d8584a2b05749ba73c37a938a` |
| updated_time | timestamp |  |  | `2026-07-26T16:54:25.13Z` |
| name | string |  |  | `Request Token` |
| symbol | string |  |  | `REQ` |
| decimals | int |  |  | `18` |

## SQL Transform

### Header

| Key | Value |
|---|---|
| frequent_type | `block` |
| list_input_tables | `ethereum_decoded.erc20_evt_transfer` |
| register_evm_call | `erc20` |
| max_num_files | `200` |
| output_table | `ethereum_contract.erc20_tokens` |
| write_mode | `Append` |
| number_index_columns | `1` |

### SQL Body

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