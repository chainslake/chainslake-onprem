$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name EthereumDecodedErc20EvtTransfer \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.table_name=erc20_evt_transfer" \
    --conf "spark.app_properties.config_file=ethereum/application.properties" \
    --conf "spark.app_properties.sql_file=evm_contract/decode_log.sql"