#!/bin/bash
export JAVA_HOME=/lib/java-8-jre
export PATH=$PATH:$JAVA_HOME/bin
export HADOOP_HOME=/lib/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
export HDFS_NAMENODE_USER="hdfs"
export HDFS_SECONDARYNAMENODE_USER="hdfs"
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
if [ ! -d "/hadoop_data/hdfs/hadoop/dfs/name/current" ]; then
  echo "Formatting NameNode..."
  $HADOOP_HOME/bin/hdfs namenode -format
fi
exec hdfs namenode
