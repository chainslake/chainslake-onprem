docker run -i -d --name chainslake_onprem lakechain/chainslake /bin/bash
docker cp chainslake_onprem:/home/hadoop ./home
docker stop chainslake_onprem
docker rm chainslake_onprem
mkdir hadoop_data_node01
mkdir hadoop_data_node02
sudo chown -R 1000:1000 hadoop_data_node01
sudo chown -R 1000:1000 hadoop_data_node02
mkdir libs
curl -o starburst-metabase-driver.jar libs/https://github.com/starburstdata/metabase-driver/releases/download/6.1.0/starburst-6.1.0.metabase-driver.jar 