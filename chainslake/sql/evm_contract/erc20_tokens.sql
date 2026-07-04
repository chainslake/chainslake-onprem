frequent_type=block
list_input_tables=${chain_name}_decoded.erc20_evt_transfer
register_evm_call=erc20
max_num_files=200
output_table=${chain_name}_contract.erc20_tokens
write_mode=Append
number_index_columns=1

===

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
