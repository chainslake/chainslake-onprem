export $(cat $CHAINSLAKE_RUN_DIR/.env) && $CHAINSLAKE_RUN_DIR/chainslake-run.sh --class chainslake.evm.Main \
    --name EthereumAddressCreator \
    --conf "spark.app_properties.app_name=evm_address.creator" \
    --conf "spark.app_properties.config_file=ethereum/application.properties"