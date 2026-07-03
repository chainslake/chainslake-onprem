export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumTransactions \
    --conf "spark.app_properties.app_name=evm.transactions" \
    --conf "spark.app_properties.rpc_list=$ETHEREUM_RPCS" \
    --conf "spark.app_properties.input_extract_transactions_table=blocks_receipt" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"