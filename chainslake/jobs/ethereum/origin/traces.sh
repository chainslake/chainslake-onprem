export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumOriginTraces \
    --conf "spark.app_properties.app_name=evm_origin.traces" \
    --conf "spark.app_properties.rpc_list=$ETHEREUM_TRACE_BLOCK_RPCS" \
    --conf "spark.app_properties.max_concurrent_blocks=100" \
    --conf "spark.app_properties.number_block_per_partition=300" \
    --conf "spark.app_properties.max_time_run=40" \
    --conf "spark.app_properties.max_retry=40" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"