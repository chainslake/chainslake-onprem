# [schema].[table_name]

## Status

<Present the following information in table form>

- Created date
- Last updated date
- Number of records
- Number of files
- Size
- frequentType
- fromBlock
- toBlock
- fromEpochSecond
- toEpochSecond

## Lineage

- Upstream tables: List of listInputTables
- Downstream tables: Compute the downstream list from the listInputTables of all tables

## Schema 

Show the columns, types, and examples in a single information table

## SQL Transform <If any>

Show the SQL code in sqlSource; note that the following replacements must be performed:
    - @ -> $
    - [nl] -> \n
    - ` -> '

```sql
<Put the code here>
```

## ABI <If any>

Each ABI group is displayed under the `### <abi_name>` heading.
Each event/function is displayed under a `####` heading with its signature, along with its own JSON code block.

Example:
### erc20

#### `Transfer(indexed address from, indexed address to, uint256 value)` — event

```json
{
  "anonymous": false,
  "inputs": [...],
  "name": "Transfer",
  "type": "event"
}
```

#### `balanceOf(address _owner) returns (uint256)` — view function

```json
{
  "constant": true,
  "name": "balanceOf",
  ...
}
```
