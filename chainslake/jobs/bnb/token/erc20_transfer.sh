$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name BnbTokenErc20Transfer \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.config_file=bnb/application.properties" \
    --conf "spark.app_properties.sql_file=evm_token/erc20_transfer.sql"