Read the README.md file to understand the project context
- I need the ethereum_token.erc20_transfer data table, which takes input from 2 tables: ethereum.transactions, ethereum_decoded.erc20_evt_transfer
- The 2 input tables will be joined on block_number, tx_hash (from transfer) - hash (transactions)
- Take all columns of the transfer table, and also take the following information from the transactions table:
    - from: rename it to tx_from
    - to: rename it to tx_to 
    - method_id: rename it to tx_method_id
- The code must follow the project conventions
- After development is done, let me review the code before testing the job by running it manually

===

Read the README.md file to understand the project context
- In the current data warehouse there is the ethereum_token.erc20_transfer table, however it does not yet have the token_symbol information. I want you to modify the job code of this table to add an additional input from the ethereum_contract.erc20_tokens table (join on contract_address)
- Add the symbol and decimals from erc20_tokens to the erc20_transfer table, and also recalculate the value using the following formula:
    value = value * 10 ^ -decimals
- The code must follow the project conventions
- After development is done, let me review the code before testing the job by running it manually

===

- I have written a Python script get_example_table.py to retrieve 1 record from a data table in the data warehouse, in order to get the schema and an example from a table. I need you to write a few more scripts as follows:
    - A script to drop a data table; calling this script must require the user to confirm the deletion
    - A script to execute a query on the data warehouse:
        - it must check that if the query modifies data (delete, update), it is blocked from execution
        - the query must have a limit on the number of records returned
- After finishing, write me a README.md file with usage instructions for all 3 scripts (including the get_example_table.py script)

===

Read the README.md file to understand the project context
- I want a Data Agent that can help me maintain this project, with the ability to learn automatically and enrich its skills over time. Please write an AGENT_INSTRUCTION.md for me as the starting point for this Agent.
- In addition to the directories of this project, the Agent also manages 2 more directories:
    - script: This directory contains .py Python scripts and 1 index.md file with a short description of each script in the directory
        - While working, if the Agent finds that a task is repetitive or requires special tools (e.g. calling an API...), it will automatically write that Python script for reuse, then add a short description of the tool to the index.md file so that next time it only needs to read the index.md file to reuse the script without rewriting it. 
    - skill: This is where skills, i.e. the Agent's experience accumulated during work, are stored; each skill is a .md file and there is an index.md file containing short descriptions of all the skills
        - In use, the user will write a prompt to ask the agent to execute a task; after the task is completed successfully, the Agent will proactively write a skill for that task, so that next time the user asks, the Agent can do it immediately without the user's guidance
- All scripts and skills are written proactively and automatically by the Agent without direct requests from the user, with the aim of letting the Agent enrich its own tools and skills to better serve the user.

===

Read the AGENT_INSTRUCTION.md file to understand the context
- Your task is to help me build a new data pipeline for the BNB chain, similar to ethereum
- For the BNB chain to work, you need to find a list of RPCs to add to the chainslake-run/.env file (similar to ETHEREUM_RPCS)
    - Here is the approach:
        - Get the list of free RPCs from the site: https://chainlist.org/rpcs.json
        - Get the RPC list for the chain name: BNB Smart Chain Mainnet
        - For each RPC, check whether it meets the usage requirements by calling the following APIs as a test:
            - API to get the latest block
            ```sh
            curl -X POST "<<RPC to check>>" \
                -H "Content-Type: application/json" \
                -d '{
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }'
            ```
            The output should be returned like the following example:
            ```json
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": "0x15536ee"
            }
            ```
            - API to get transaction_blocks (used for the _origin.transaction_blocks table); use the result from the previous step to call the API
            ```sh     
            curl -X POST "<<RPC to check>>" \
            -H "Content-Type: application/json" \
            -d '{
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [
                "0x15536ee",
                true
            ],
            "id": 1
            }'
            ```
            Verify that the returned result has the following format:
            ```json
            {
                "result": {
                    var number: String,
                    var hash: String,
                    var parentHash: String,
                    var nonce: String,
                    var sha3Uncles: String,
                    var logsBloom: String,
                    var transactionsRoot: String,
                    var stateRoot: String,
                    var receiptRoot: String,
                    var miner: String,
                    var mixHash: String,
                    var difficulty: String,
                    var totalDifficulty: String,
                    var extraData: String,
                    var size: String,
                    var gasLimit: String,
                    var gasUsed: String,
                    var timestamp: String,
                    var transactions: Array[{
                        var hash: String,
                        var nonce: String,
                        var blockHash: String,
                        var blockNumber: String,
                        var transactionIndex: String,
                        var from: String,
                        var to: String,
                        var value: String,
                        var gasPrice: String,
                        var gas: String,
                        var input: String,
                        var r: String,
                        var s: String,
                        var type: String
                    }]
                }
            }
            ```
            - API to get blocks receipt, used for the origin.blocks_receipt table; use the latest block to call the API
            ```sh
            curl -X POST "<<RPC to check>>" \
            -H "Content-Type: application/json" \
            -d '{
            "jsonrpc": "2.0",
            "method": "eth_getBlockReceipts",
            "params": [
                "0x15536ee"
            ],
            "id": 1
            }'
            ```
            Verify that the returned result has the following format:
            ```json
            {
                "result": Array[{
                    var blockHash: String,
                    var blockNumber: String,
                    var contractAddress: String,
                    var cumulativeGasUsed: String,
                    var effectiveGasPrice: String,
                    var from: String,
                    var gasUsed: String,
                    var to: String,
                    var status: String,
                    var transactionHash: String,
                    var transactionIndex: String,
                    var `type`: String,
                    var logsBloom: String,
                    var logs: Array[{
                        var address: String,
                        var topics: Array[String],
                        var data: String,
                        var blockNumber: String,
                        var transactionHash: String,
                        var transactionIndex: String,
                        var blockHash: String,
                        var blockTimestamp: String,
                        var logIndex: String,
                        var removed: Boolean
                    }]
                }]
            }
            ```
    - After passing the check, the RPCs will be added to BNB_RPCS for the job to use

=== 

Read the AGENT_INSTRUCTION.md file to understand the context
- Install the Chainslake data warehouse
- Also help me set up the admin account for Metabase, 
- Then start the Ethereum workflow (run it only once)
- Check the data of the tables after running

- I believe you have gained a lot of experience handling this task, so please write them down as scripts and skills for future use
- I think the password and the login account for Metabase should not be hard-coded directly in the script like that; put them in the .env file, and don't forget to add it to .gitignore so sensitive information is not pushed to git

===

Read the AGENT_INSTRUCTION.md file to understand the context
- I want you to write some query tools to support maintaining the data warehouse as follows:
    - Tool to check the properties of a table:
        - How it works: run a SQL query using the spark engine: "show tblproperties <table name>"
        - The result shows the properties of the table, including these important ones:
            - isLock: Indicates whether the table is locked (value 1 or 0), ensuring that only 1 job writes data to the table at a time; if a job writes to a locked table it will report the error Table is Lock
            - frequenceType: The frequenceType of the table, which can be one of the following values: block, hour, minute, day
            - fromBlock, toBlock: If the frequenceType is block, these 2 values will exist, 
                - they indicate the range of blocks that the table currently holds data for
                - these values are only updated if the write succeeds (ensuring accurate data for downstream consumers)
                - downstream jobs rely on fromBlock and toBlock to compute the appropriate from and to values when running
            - fromEpochSecond, toEpochSecond: similar to fromBlock and toBlock but used for tables whose frequenceType is minute, hour, day. They use seconds as the unit instead of blocks
    - Tool to unlock a table:
        - How it works: run SQL using the spark engine: "alter table <table name> set tblproperties (isLock=0)"
        - Notes:
            - this tool is used when a job writing data to a table fails, and re-running it reports the error Table is Lock (because the table was not unlocked on the previous run)
            - only use this tool when you are sure that no job is still writing data to the table

===

Read the AGENT_INSTRUCTION.md file to understand the context
- I need to upload the file data/eth_etf_address.csv into the data warehouse, following these steps:
    - Create a new schema named ext_upload (if it does not exist yet) using the spark query engine:
        SQL: `create schema ext_upload`
    - Copy the file to node01, then use hdfs put (inside the docker node01) to push it to hdfs
        script: `hdfs dfs -put eth_etf_address.csv /user/hive/warehouse/ext_upload.db/eth_etf_address/`
    - Create the table using SQL with the spark engine:
       ```sql
       CREATE EXTERNAL TABLE ext_upload.eth_etf_address (
            issuer STRING,
            address STRING,
            etf_ticker STRING,
            track_inflow STRING,
            track_outflow STRING,
            inverse_values STRING
        )
        ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
        WITH SERDEPROPERTIES (
            "separatorChar" = ",",
            "quoteChar"     = "\""
        )
        STORED AS TEXTFILE
        LOCATION 'hdfs:///user/hive/warehouse/ext_upload.db/eth_etf_address/';
       ``` 
    - Query the table to verify it works
- After finishing, write the skills and scripts for reuse
- since the chainslake directory is already mounted into node01, the step of copying into node01 can be skipped
- instead, create a new directory called ext_upload inside the chainslake directory, so users can drop the files they want to upload there

===

- Read the AGENT_INSTRUCTION.md file to understand the context
- Currently I see that the scripts and skills for interacting with airflow are implemented through HTTP requests; I think this is not the optimal approach for the agent, so I want you to review and fix them to use the Airflow CLI

===

- Read the AGENT_INSTRUCTION.md file to understand the context
- Perform the metabase setup
- I want to upgrade metabase to the latest version so the Agent can use the metabase cli; you can delete the old metabase database in postgres, create a new database, and set everything up from scratch using the metabase cli
- update the skills and scripts to use the metabase cli

=== 

- I want you to write a new skill for configuring parameters for a job or pipeline
- This is a difficult but very important task, so you need to understand it thoroughly and write it out clearly.
- Recapping some important configuration parameters of a job:
    - number_block_per_partition: the number of blocks per partition
    - max_number_partition: the number of partitions processed in each iteration
    - max_time_run: the number of iterations in a single job run
- These parameters can be configured in the application.properties file, or directly in the job's .sh file via config, e.g.: --conf "spark.app_properties.max_number_partition=24"; if set in both places, the job prioritizes the value in the .sh file
- How to choose the parameters:
    - number_block_per_partition:
        - it will be chosen per chain so that each partition holds about 1 hour of data (needs to be a bit more). This number can be estimated from information found on the Internet, but afterwards it must be recalculated based on block_number and block_time by counting the number of blocks in 1 hour from the transaction_blocks table (note that you must ensure there is enough data for 1 hour)
        - The best approach when setting up a new chain is to take the number_block_per_partition value from information on the Internet, then set max_number_partition and max_time_run and run the job 1 to 2 times, then recalculate the number_block_per_partition for accuracy (remember to take a bit more, ideally 5%, because the number of blocks per hour of a chain is usually not fixed).
    - max_number_partition:
        - this parameter indicates how many partitions are processed in 1 iteration; it needs to be adjusted to fit the amount of resources (number of threads and memory provided) allocated to the job
        - Resources are allocated based on the following 2 parameters of the job:
            --master local[2] \ the more threads, the more partitions processed concurrently
            --driver-memory 4g \ the memory provided must be larger than the data read volume (if any) + the data write volume of the job
        - To compute the memory needed for the job, you need to determine the size of 1 data partition in the table, using the following SQL:
            `describe detail <table name>` Then look for sizeInBytes to know the actual size of the table
        - Important note: for jobs whose frequent_type is day, max_number_partition must be >= 24 
    - max_time_run: indicates the number of iterations in one data run; the most reasonable choice is one that lets a single run process 1 day of data
- DAG configuration
    - start_date: set it to the chain's start date, e.g. for Ethereum it is 30/07/2015
    - is_paused_upon_creation=True: so the DAG is always off on startup
    - catchup=False: so the DAG does not automatically run historical days
- Note: If the user requests data from 
- By default, we configure the run_mode of the entire pipeline as backward, i.e. running backwards from the present to the past; once there is enough data up to the day the user needs, this configuration must be switched back to forward. However, instead of switching run_mode to forward for all jobs in the pipeline, you only need to change this configuration on the first job in the pipeline, i.e. the _origin.transaction_blocks job, because once this job stops running backwards, the downstream jobs cannot continue further into the past even with backward (because there is no data). Note that the backward configuration allows a job to run both forward and backward, while forward only allows running forward.
- When adding a new job to the DAG, assuming the DAG has already finished backfilling data into the past, the newly added job must itself run back into the past; use the Airflow CLI to run a backfill for just this new job.
    
===

Please write the installation instructions as a skill, so the Agent no longer needs to read the docker/README.md file (since this is a document for users)

===

Please configure it for me so that every time opencode is opened, all logs with OPENCODE_LOG_LEVEL=TRACE are written to the opencode.log file in this directory 

===

- I want to modify the Configure Job/Pipeline Parameters skill as follows:
    - in step 4: Configure `start_date` on the DAG
        - Configure the default start_date to be 2 years from the current date
        - must add the catchup=False configuration so the DAG does not automatically run again from the start_date, since step 6 already runs the backfill

=== 

I want you to add a Use case section to AGENT_INSTRUCTION.md to give the Agent quick guidance on which skills to call in specific usage scenarios. The Use case section will also be updated automatically by the Agent during use. Here are some Use cases:
    - Starting:
        - Check whether the system has been installed; if not, ask the user if they want to install it right away
        - If it is installed, check whether the system has been started and all services are fully running; if not, ask the user if they want to start the system
    - Installing the system:
        - Use the skill: Install Chainslake On-Premises
        - After installation and startup are complete, let the user know which chains are currently available
        - Ask the user which chain they want to run or whether they want to set up a new chain
    - Setting up a new chain:
        - Use the skill: Add New Chain Pipeline (ask the user which chain they want to set up)
        - Use the skill: Configure Job/Pipeline Parameters 
            - Determine the configuration parameters needed for the new chain

===

- I need you to write a new script that collects the current status information of the data tables in the warehouse and puts it into the catalog directory of this project
- Here are the steps:
    - Get the list of all tables in the warehouse
        - since there is no single SQL statement that can retrieve all tables, the script needs to run the following 2 queries
            - `show schemas`: get the list of all schemas in the warehouse (skip the default schema)
            - `show tables in [schema_name]`: get the list of all tables in the schema
    - For each table, the script needs to collect the following information:
        - the table schema (list of columns and types) and an example of the data, using the existing script
        - the table properties, using the existing script
            - The properties to collect include:   
                - frequentType
                - fromBlock
                - toBlock
                - fromEpochSecond
                - toEpochSecond
                - listInputTables: indicates the list of upstream tables of this table
                - sqlSource: the SQL transform of the table (if any)
                - abi: the ABI used in the table (if any)
        - Table sizing information
            - the current number of records: use `select count(*) from [table_name]` to count the records
            - creation date, update date, size (sizeInBytes), number of files: use `describe detail [table_name]` to get them
    - Compile the information of each table into a document named [schema].[table_name].md using the template in table_template.md
    - Compile all upstream and downstream information of all tables to create a document named lineage.md (also placed in the catalog directory); this document shows the dependencies (lineage) of all tables as a visual graph 
            
