spark-submit --master local[2] \
    --driver-memory 4g \
    --deploy-mode client \
    "$@" \
    --conf "spark.app_properties.chainslake_home_dir=$CHAINSLAKE_HOME_DIR" \
    --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" \
    --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
    --conf spark.databricks.delta.retentionDurationCheck.enabled=false \
    --conf spark.scheduler.mode=FAIR \
    --jars $CHAINSLAKE_RUN_DIR/chainslake-deps.jar \
    $CHAINSLAKE_RUN_DIR/chainslake.jar