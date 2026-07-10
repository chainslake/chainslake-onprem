$CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.sql.Main \
    --name BnbDecodedLog \
    --conf "spark.app_properties.app_name=sql.transformer" \
    --conf "spark.app_properties.table_name=$1" \
    --conf "spark.app_properties.config_file=bnb/application.properties" \
    --conf "spark.app_properties.run_mode=$2" \
    --conf "spark.app_properties.sql_file=evm_contract/decode_log.sql"