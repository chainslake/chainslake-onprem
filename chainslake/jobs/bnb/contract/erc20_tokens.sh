export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --master local[10] \
    --name BnbERC20Tokens \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.config_file=bnb/application.properties" \
    --conf "spark.app_properties.rpc_list=$BNB_RPCS" \
    --conf "spark.app_properties.sql_file=evm_contract/erc20_tokens.sql"