# User Acceptance Testing

## [shema].[table]

- Job config
    - number_block_per_partition:
    - max_number_partition: 24
    - max_time_run: 5
    - run_mode: backward
- Resource config <<nếu job không chạy thành công do thiếu tài nguyên thì cần điều chỉnh lại>>
    --master local[2]
    --driver-memory 4g
- Result
    - fromBlock - toBlock hoặc fromDate -> toDate (tính ra từ fromEpochSecond, toEpochSecond)
    - Time to run (minute):
    - Output size of table (MB): 
