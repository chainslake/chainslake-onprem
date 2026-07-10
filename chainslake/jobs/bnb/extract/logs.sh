export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name BnbLogs \
    --conf "spark.app_properties.app_name=evm.logs" \
    --conf "spark.app_properties.rpc_list=$BNB_RPCS" \
    --conf "spark.app_properties.input_extract_logs_table=blocks_receipt" \
    --conf "spark.app_properties.config_file=bnb/application.properties"