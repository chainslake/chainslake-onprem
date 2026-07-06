frequent_type=block
list_input_tables=${chain_name}.transactions,${chain_name}_decoded.erc20_evt_transfer,${chain_name}_contract.erc20_tokens
transactions=${chain_name}.transactions
erc20_evt_transfer=${chain_name}_decoded.erc20_evt_transfer
erc20_tokens=${chain_name}_contract.erc20_tokens
output_table=${chain_name}_token.erc20_transfer
re_partition_by_range=block_date,block_number
partition_by=block_date
write_mode=Append
number_index_columns=3

===

with erc20_evt_transfer as (
    select block_date, block_number, block_time, updated_time
        , contract_address, tx_hash, evt_index
        , `from`, `to`, value
    from ${erc20_evt_transfer}
    where block_number >= ${from} and block_number <= ${to}
)
, transactions as (
    select block_number, hash
        , `from` as tx_from
        , `to` as tx_to
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
    , t.`from`
    , t.`to`
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
