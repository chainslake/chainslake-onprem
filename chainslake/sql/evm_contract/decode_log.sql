frequent_type=block
list_input_tables=${chain_name}.logs
logs_table_name=${chain_name}.logs
pre_decode_tables=${table_name}
output_table=${chain_name}_decoded.${table_name}
re_partition_by_range=block_date,block_time
partition_by=block_date
write_mode=Append
number_index_columns=3

===

select * from ${pre_decode_tables}