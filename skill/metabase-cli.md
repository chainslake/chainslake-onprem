# Skill: Metabase CLI (`mb`) — Quản lý nội dung Metabase

## Mô tả
Sử dụng Metabase CLI (`mb`) để quản lý databases, cards, dashboards, collections, transforms, và tìm kiếm nội dung trên Metabase on-premise. CLI là công cụ chính để Agent thao tác với Metabase thay vì gọi API trực tiếp.

## Điều kiện áp dụng
- Metabase CLI đã cài đặt: `npm install -g @metabase/cli`
- Đã authenticate: `mb auth login --url http://localhost:53000 --api-key <KEY>`
- Metabase v0.58+ (hiện tại v0.62.4.3)

## Quy tắc chung

### Output format
- Mặc định: text humans-readable
- Thêm `--json` để lấy JSON (dùng cho script/agent)
- `--full` để lấy đầy đủ fields
- `--fields a,b,c` để project cụ thể

### Kiểm tra auth trước khi thao tác
```bash
mb auth status --json
```
Nếu chưa authenticate → `mb auth login --url http://localhost:53000 --api-key <KEY>`

---

## Các bước thực hiện

### 1. Database Operations

```bash
# Liệt kê tất cả databases
mb db list

# Xem chi tiết database (kèm danh sách tables)
mb db get <db-id> --include tables

# Liệt kê schemas trong database
mb db schemas <db-id>

# Liệt kê tables trong một schema
mb db schema-tables <db-id> <schema-name>

# Đồng bộ schema thủ công (khi thêm bảng mới)
mb db sync-schema <db-id>

# Quét lại field values (khi dữ liệu thay đổi)
mb db rescan-values <db-id>
```

**V Chainslake projects:**
- Database SparkSQL = id 2
- Database Trino = id 3

```bash
# Đồng bộ schema cho Spark
mb db sync-schema 2

# Xem tất cả schemas trong Spark
mb db schemas 2

# Xem tables trong schema ethereum
mb db schema-tables 2 ethereum
```

### 2. Table & Field Metadata

```bash
# Liệt kê tables (có thể filter theo database)
mb table list --db-id 2

# Xem chi tiết table kèm fields
mb table get <table-id> --include fields

# Liệt kê fields của table
mb table fields <table-id>

# Cập nhật display name, description cho table
mb table update <table-id> --body '{"display_name":"Blocks","description":"Ethereum blocks data"}'

# Xem field details
mb field get <field-id>

# Cập nhật field metadata (semantic type, description)
mb field update <field-id> --body '{"semantic_type":"type/PK","description":"Block number"}'

# Xem cached distinct values
mb field values <field-id>

# Xem cardinality
mb field summary <field-id>
```

### 3. Cards (Questions, Models, Metrics)

```bash
# Liệt kê cards
mb card list

# Xem chi tiết card
mb card get <card-id>

# Tạo card mới (native SQL question)
mb card create --body '{
  "name": "Top 10 Tokens",
  "dataset_query": {
    "type": "native",
    "native": {
      "query": "SELECT token_address, COUNT(*) as transfers FROM ethereum_token.erc20_transfer GROUP BY token_address ORDER BY transfers DESC LIMIT 10",
      "template-tags": {}
    },
    "database": 2
  },
  "display": "table",
  "visualization_settings": {}
}'

# Tạo card (MBQL question)
mb card create --body '{
  "name": "Recent Blocks",
  "dataset_query": {
    "type": "query",
    "query": {
      "source-table": 10,
      "order-by": [["desc", ["field", 100]]],
      "limit": 20
    },
    "database": 2
  },
  "display": "table"
}'

# Chạy card và lấy kết quả JSON
mb card query <card-id> --export-format json

# Export card ra CSV
mb card query <card-id> --export-format csv > result.csv

# Cập nhật card
mb card update <card-id> --body '{"name":"Updated Name"}'

# Archive card (soft-delete)
mb card archive <card-id>
```

### 4. Dashboards

```bash
# Liệt kê dashboards
mb dashboard list

# Xem dashboard kèm dashcards
mb dashboard get <dashboard-id>

# Tạo dashboard mới
mb dashboard create --body '{
  "name": "Ethereum Overview",
  "description": "Overview of Ethereum blockchain data"
}'

# Thêm dashcard vào dashboard
mb dashboard update <dashboard-id> --body '{
  "dashcards": [
    {
      "card_id": 1,
      "col": 0, "row": 0,
      "size_x": 12, "size_y": 6
    },
    {
      "card_id": 2,
      "col": 12, "row": 0,
      "size_x": 12, "size_y": 6
    }
  ]
}'
# Grid 24 columns. size_x=24 = full width, size_x=12 = half

# Cập nhật 1 dashcard cụ thể
mb dashboard update-dashcard <dashboard-id> <dashcard-id> --body '{
  "col": 0, "row": 6, "size_x": 24, "size_y": 4
}'

# Thêm filter (parameter) vào dashboard
mb dashboard update <dashboard-id> --body '{
  "parameters": [
    {
      "id": "chain_filter",
      "name": "Chain",
      "type": "string/=",
      "sectionId": "string"
    }
  ]
}'

# Xem giá trị selectable cho parameter
mb dashboard parameter-values <dashboard-id> <parameter-id>

# Archive dashboard
mb dashboard archive <dashboard-id>
```

### 5. Collections

```bash
# Liệt kê collections
mb collection list

# Xem tree hierarchy (JSON only)
mb collection tree --json

# Xem items trong collection
mb collection items <collection-id>

# Tạo collection mới
mb collection create --body '{
  "name": "Ethereum Analytics",
  "description": "Dashboards and questions for Ethereum"
}'

# Archive collection
mb collection archive <collection-id>
```

### 6. Search

```bash
# Tìm kiếm nội dung
mb search "ethereum"

# Tìm kiếm theo loại
mb search "blocks" --models card
mb search "overview" --models dashboard
mb search "ethereum" --models collection
```

### 7. Settings

```bash
# Liệt kê tất cả settings
mb setting list

# Xem setting cụ thể
mb setting get site-name

# Đổi setting
mb setting set site-name '"Chainslake Warehouse"'
# Lưu ý: giá trị phải là JSON hợp lệ — string cần quotes kép
```

### 8. Snippets (Native Query)

```bash
# Liệt kê snippets
mb snippet list

# Tạo snippet mới
mb snippet create --body '{
  "name": "ethereum_tables",
  "description": "List of ethereum tables",
  "content": "SELECT table_name FROM information_schema.tables WHERE table_schema = '\''ethereum'\''"
}'

# Cập nhật snippet
mb snippet update <snippet-id> --body '{"content":"..."}'

# Archive snippet
mb snippet archive <snippet-id>
```

### 9. Segments & Measures

```bash
# Segments (saved filters)
mb segment list
mb segment create --body '{
  "name": "High Value Transfers",
  "description": "Transfers > 100 ETH",
  "definition": {
    "filter": [">", ["field", 100], 100000000000000000000]
  }
}'

# Measures (saved aggregations)
mb measure list
mb measure create --body '{
  "name": "Total Transfer Volume",
  "definition": {
    "aggregation": ["sum", ["field", 101]]
  }
}'
```

### 10. Upload CSV

```bash
# Upload CSV mới (tạo table + model)
mb upload csv --file data.csv

# Append vào table đã có
mb upload append <table-id> --file new_data.csv

# Replace dữ liệu table
mb upload replace <table-id> --file updated_data.csv
```

---

## Workflow thường gặp

### Kiểm tra dữ liệu mới sau khi chạy pipeline
```bash
# 1. Đồng bộ schema
mb db sync-schema 2

# 2. Tìm table mới
mb search "blocks" --models table

# 3. Xem fields của table
mb table get <table-id> --include fields
```

### Tạo dashboard từ đầu
```bash
# 1. Tạo collection
COLLECTION_ID=$(mb collection create --body '{"name":"My Dashboard"}' --json | jq -r '.id')

# 2. Tạo cards
CARD1=$(mb card create --body '{"name":"Card 1",...}' --json | jq -r '.id')
CARD2=$(mb card create --body '{"name":"Card 2",...}' --json | jq -r '.id')

# 3. Tạo dashboard với dashcards
mb dashboard create --body "{
  \"name\": \"My Dashboard\",
  \"collection_id\": $COLLECTION_ID,
  \"dashcards\": [
    {\"card_id\": $CARD1, \"col\": 0, \"row\": 0, \"size_x\": 12, \"size_y\": 6},
    {\"card_id\": $CARD2, \"col\": 12, \"row\": 0, \"size_x\": 12, \"size_y\": 6}
  ]
}"
```

### Export kết quả query
```bash
# Chạy card và export CSV
mb card query 42 --export-format csv > result.csv

# Chạy native SQL qua query command
mb query --body '{
  "type": "native",
  "native": {"query": "SELECT * FROM ethereum.blocks LIMIT 10"},
  "database": 2
}' --json
```

---

## Lưu ý / Gotchas

### Grid layout cho dashboards
- Dashboard grid **24 columns** wide
- `size_x = 24` → full width
- `size_x = 12` → half width
- `col + size_x ≤ 24`, không overlap

### `mb setup` chỉ dùng 1 lần
- `mb setup` chỉ chạy trên instance **chưa setup**
- Nếu đã có admin → lỗi

### API key vs Browser OAuth
- `mb auth login --api-key <KEY>` — headless, phù hợp CI/agent
- `mb auth login` (không --api-key) — mở browser OAuth (cần v0.62+)

### Body JSON format
- Create/update nhận body qua `--body '<JSON>'` hoặc `--file <path>`
- String values cần quotes kép: `'"value"'`
- Boolean: `true`/`false`
- Number: bare

### Entity ID
- Metabase dùng entity_id (NanoID) cho many resources
- Dùng `mb eid --model <model> <eid>` để convert sang numeric id
- Entity ID có thể bắt đầu bằng `-` → dùng `--body` thay vì positional arg

---

## Ví dụ thực tế
- Ngày: 2026-07-12
- Metabase v0.62.4.3 OSS
- Metabase CLI v0.2.1
- Dùng để: sync schema, tìm tables, tạo cards, quản lý dashboards
