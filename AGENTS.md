# Chainslake Data Team — Shared Rules

## Project Context
Chainslake On-Premises Blockchain Data Warehouse.
Chi tiết kiến trúc: đọc AGENT_INSTRUCTION.md.

## Conventions (từ AGENT_INSTRUCTION.md section 4)
- Pipeline structure: `chainslake/jobs/<chain_name>/{origin,extract,contract,token}/`
- SQL format: header (key=value) + `===` + body
- Naming: `<chain>_origin`, `<chain>`, `<chain>_decoded`, `<chain>_contract`, `<chain>_token`
- DAG: 1 per chain, schedule "10 0 * * *", max_active_runs=1
- Biến SQL: `${chain_name}`, `${from}`, `${to}`, `${table_name}`

## Thư mục tài liệu bài toán (`docs/`)
- Mỗi bài toán có thư mục riêng trong `docs/<problem-name>/`
- `docs/index.md` — index tất cả bài toán, luôn cập nhật khi có bài mới
- `docs/<problem-name>/Data_Requirement.md` — yêu cầu từ User (BA viết, theo template `template/data_requirement.md`)
- `docs/<problem-name>/design/` — thiết kế bảng từ Data Architect (theo format catalog / template `template/table_catalog.md`)
- `docs/<problem-name>/development.md` — thông tin chạy job từ Developer (theo template `template/development.md`)
- `docs/<problem-name>/UAT.md` — kết quả chạy test 5 ngày + cấu hình job từ DataOps (theo template `template/UAT.md`)
- `docs/<problem-name>/test/` — test cases từ Tester (theo template `template/TestCase.md`)

## Vòng lặp Dev-Tester
- Developer dev job → Tester test → nếu FAIL → Developer fix → Tester test lại
- Tối đa 3 vòng lặp. Nếu vẫn FAIL → thông báo User xử lý
- Sau Dev-Tester PASS → DataOps chạy UAT 5 ngày, cập nhật UAT.md
- Sau UAT PASS → DataOps triển khai daily + thêm DAG
- Template: `template/data_requirement.md`, `template/table_catalog.md`, `template/UAT.md`

## Tools Reference
| Tool | Path |
|---|---|
| Query data | `python query/query_table.py "<SQL>"` |
| Get schema | `python query/get_example_table.py <table>` |
| DDL | `python query/ddl_spark.py "<SQL>"` |
| Drop table | `python query/drop_table.py <table>` |
| Trigger DAG | `python script/trigger_dag.py <dag_id>` |
| Build catalog | `python script/build_catalog.py` |

## Agent Collaboration Rules
- Khi team-lead giao task, đọc skill liên quan trước khi bắt đầu
- Luôn đọc file mẫu tương tự trước khi tạo file mới
- Review code trước khi submit kết quả
- Nếu gặp lỗi, tự phân tích log trước khi escalate
- Sau mỗi task thành công, cập nhật skill nếu cần
- Luôn làm việc trong thư mục bài toán (`docs/<problem-name>/`)
- Developer dùng `_dev` suffix cho tất cả bảng và code đang phát triển
- Developer KHÔNG được sửa DAG, chỉ dev code job
