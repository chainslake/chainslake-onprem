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
$HIVE_HOME/bin/schematool -dbType postgres -info > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "First time initialization: Running initSchema..."
  $HIVE_HOME/bin/schematool -dbType postgres -initSchema
fi

exec hive --service metastore
