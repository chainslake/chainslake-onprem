# ethereum_token.erc20_transfer

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | 2026-07-12 15:54:30 |
| Ngày update gần nhất | 2026-07-13 00:18:35 |
| Số bản ghi | 463035 |
| Số file | 6 |
| Dung lượng | 35.2 MB |
| frequentType | block |
| fromBlock | 25516917 |
| toBlock | 25517819 |
| fromEpochSecond | N/A |
| toEpochSecond | N/A |

## Lineage

- **Upstream tables**: ethereum.transactions, ethereum_decoded.erc20_evt_transfer, ethereum_contract.erc20_tokens
- **Downstream tables**: _None_

## Schema

| Column | Type | Example |
|---|---|---|
| block_date | date | `2026-07-12T00:00:00Z` |
| block_number | bigint | `25517218` |
| block_time | timestamp | `2026-07-12T14:44:23Z` |
| updated_time | timestamp | `2026-07-12T15:49:46.398Z` |
| contract_address | string | `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` |
| symbol | string | `USDC` |
| decimals | int | `6` |
| tx_hash | string | `0x02bd3e963637b1d42adc792b006c8bae68a1d3c921511e390547afa962fbdf84` |
| evt_index | int | `0` |
| from | string | `0x98908f7d33e88479e4e6d1c1e6eb8997a2bdb94c` |
| to | string | `0x6cdb7776f6a20b9ed4441b791e9541a6fc04e313` |
| value | double | `2903.2391629999997` |
| tx_from | string | `0x98908f7d33e88479e4e6d1c1e6eb8997a2bdb94c` |
| tx_to | string | `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` |
| tx_method_id | string | `0xa9059cbb` |

## SQL Transform

```sql


with erc20_evt_transfer as (
    select block_date, block_number, block_time, updated_time
        , contract_address, tx_hash, evt_index
        , 'from', 'to', value
    from ${erc20_evt_transfer}
    where block_number >= ${from} and block_number <= ${to}
)
, transactions as (
    select block_number, hash
        , 'from' as tx_from
        , 'to' as tx_to
        , method_id as tx_method_id
    from ${transactions}
    where block_number >= ${from} and block_number <= ${to}
)
, erc20_tokens as (
    select contract_address
        , symbol
        , decimals
    from ${erc20_tokens}
)

select t.block_date
    , t.block_number
    , t.block_time
    , t.updated_time
    , t.contract_address
    , tk.symbol
    , tk.decimals
    , t.tx_hash
    , t.evt_index
    , t.'from'
    , t.'to'
    , cast(t.value as double) * pow(10, -tk.decimals) as value
    , tx.tx_from
    , tx.tx_to
    , tx.tx_method_id
from erc20_evt_transfer t
inner join transactions tx
on t.block_number = tx.block_number
and t.tx_hash = tx.hash
left join erc20_tokens tk
on t.contract_address = tk.contract_address

```
