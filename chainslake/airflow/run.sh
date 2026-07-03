rm airflow-webserver.pid
rm -rf ./logs
export AIRFLOW_HOME=/home/hadoop/projects/chainslake/airflow
airflow standalone
