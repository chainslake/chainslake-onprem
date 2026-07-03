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
export TRINO_HOME=/lib/trino
export PATH=$TRINO_HOME/bin:$PATH
export PATH=$PATH:/home/hadoop/.local/bin
export PYTHONPATH=/home/hadoop/.local/lib/python3.8/site-packages
exec /home/hadoop/projects/chainslake/airflow/run.sh
