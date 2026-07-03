#!/bin/bash
export JAVA_HOME=/lib/java-8-jre
export PATH=$PATH:$JAVA_HOME/bin
export HADOOP_HOME=/lib/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
export HDFS_NAMENODE_USER="hdfs"
export HDFS_SECONDARYNAMENODE_USER="hdfs"
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export SPARK_HOME=/lib/spark
export PATH=$PATH:$SPARK_HOME/bin
export HIVE_HOME=/lib/hive
export PATH=$HIVE_HOME/bin:$PATH
exec spark-submit --name SparkThriftServer --class org.apache.spark.sql.hive.thriftserver.HiveThriftServer2 \
    --master local[2] --deploy-mode client \
    --driver-memory 2g \
    --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" \
    --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
    --conf spark.databricks.delta.retentionDurationCheck.enabled=false \
    --conf spark.databricks.delta.metadataColumn.enabled=true
