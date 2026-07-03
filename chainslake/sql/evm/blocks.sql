frequent_type=block
list_input_tables=${chain_name}_origin.transaction_blocks,${chain_name}_origin.blocks_receipt
transaction_blocks=${chain_name}_origin.transaction_blocks
blocks_receipt=${chain_name}_origin.blocks_receipt
output_table=${chain_name}.blocks
re_partition_by_range=block_date,block_number
partition_by=block_date
write_mode=Append
number_index_columns=3

===

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
