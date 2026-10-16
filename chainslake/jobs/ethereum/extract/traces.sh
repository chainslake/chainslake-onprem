export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumTraces \
    --conf "spark.app_properties.app_name=evm.traces" \
    --conf "spark.app_properties.rpc_list=$ETHEREUM_TRACE_BLOCK_RPCS" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"