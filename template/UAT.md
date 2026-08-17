# User Acceptance Testing

## [schema].[table]

- Job config
    - number_block_per_partition:
    - max_number_partition: 24
    - max_time_run: 5
    - run_mode: backward
- Resource config <<adjust if job fails due to insufficient resources>>
    --master local[2]
    --driver-memory 4g
- Result
    - fromBlock - toBlock or fromDate -> toDate (calculated from fromEpochSecond, toEpochSecond)
    - Time to run (minute):
    - Output size of table (MB): 