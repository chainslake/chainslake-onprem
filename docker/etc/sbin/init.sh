#!/bin/sh
if [ ! -d "/hadoop_data/hdfs/hadoop" ]; then
  echo "Change permission"
  chown -R 1000:1000 /hadoop_data
  chmod -R 770 /hadoop_data
fi
