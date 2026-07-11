# Skill: Upload CSV to Data Warehouse

## Mô tả
Upload file CSV từ máy local vào Data Warehouse thông qua HDFS, tạo external table để query.

## Điều kiện áp dụng
- Cần import file CSV vào data warehouse
- File CSV nằm trong thư mục `chainslake/ext_upload/` của project

## Các bước thực hiện

### Bước 1: Tạo schema (nếu chưa có)

```bash
python query/ddl_spark.py "CREATE SCHEMA IF NOT EXISTS <schema_name>"
```

### Bước 2: Upload file lên HDFS

```bash
docker exec -u hadoop chainslake-onprem-node01-1 bash -c \
  "export PS1='something' && source /etc/bash.bashrc && \
   hdfs dfs -mkdir -p /user/hive/warehouse/<schema_name>.db/<table_name> && \
   hdfs dfs -put /home/hadoop/projects/chainslake/ext_upload/<file_name>.csv /user/hive/warehouse/<schema_name>.db/<table_name>/"
```

### Bước 3: Tạo external table

```bash
python query/ddl_spark.py "
CREATE EXTERNAL TABLE <schema_name>.<table_name> (
    col1 STRING,
    col2 STRING,
    ...
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    \"separatorChar\" = \",\",
    \"quoteChar\"     = \"\"\"
)
STORED AS TEXTFILE
LOCATION 'hdfs:///user/hive/warehouse/<schema_name>.db/<table_name>/'
"
```

### Bước 4: Verify dữ liệu

```bash
python query/query_table.py "SELECT * FROM <schema_name>.<table_name> LIMIT 10"
```

## Lưu ý / Gotchas

- **Thư mục ext_upload**: Nằm tại `chainslake/ext_upload/` và đã mount sẵn vào container node01 tại `/home/hadoop/projects/chainslake/ext_upload/`. Người dùng chỉ cần bỏ file vào thư mục `chainslake/ext_upload/` trên máy host.
- **Cập nhật dữ liệu**: Nếu chỉ thay đổi nội dung file (không đổi cấu trúc columns), chỉ cần upload lại file lên HDFS là được, không cần xóa bảng tạo lại.
- **Metabase API vs SparkSQL**: DDL cần chạy qua `query/ddl_spark.py` (dùng Metabase API) hoặc `spark-sql` trên node trực tiếp. `query/query_table.py` chặn DDL.
- **OpenCSVSerde**: Dùng cho file CSV có header. Nếu file không có header, cần thêm `"skip.header.line.count" = "1"` vào SERDEPROPERTIES.

## Ví dụ thực tế
- Upload `eth_etf_address.csv` vào `ext_upload.eth_etf_address` (2026-07-11)
