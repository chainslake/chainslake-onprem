# Skill: Build Data Warehouse Catalog

## Mô tả
Tạo tài liệu catalog markdown cho toàn bộ bảng trong data warehouse, bao gồm metadata, schema, ví dụ dữ liệu và lineage graph.

## Điều kiện áp dụng
- Khi người dùng yêu cầu tạo/cập nhật catalog warehouse
- Khi cần snapshot trạng thái hiện tại của tất cả bảng trong DWH
- Sau khi thêm pipeline mới để cập nhật catalog

## Các bước thực hiện

### Bước 1: Chạy script build_catalog.py
```bash
python script/build_catalog.py
```

Tham số tùy chỉnh:
- `--skip-count`: Bỏ qua đếm rows (chạy nhanh hơn, useful khi warehouse lớn)
- `--skip-example`: Bỏ qua lấy ví dụ dữ liệu
- `--output-dir <path>`: Chỉ định thư mục output khác (mặc định: `catalog/`)

### Bước 2: Kiểm tra output
Thư mục `catalog/` sẽ chứa:
- `lineage.md`: Biểu đồ Mermaid graph thể hiện upstream/downstream
- `[schema].[table].md`: File markdown per-table với:
  - Trạng thái (ngày tạo, update, rows, files, size, block range)
  - Lineage (upstream/downstream)
  - Schema (columns + types)
  - Ví dụ dữ liệu
  - SQL Transform (nếu có trong tblproperties)
  - ABI (nếu có trong tblproperties)

### Bước 3: Review và commit
```bash
git add catalog/
git commit -m "Update DWH catalog"
```

## Lưu ý / Gotchas
- Script đọc `METABASE_API_KEY` từ `query/.env` — cần đảm bảo file này tồn tại và hợp lệ
- Script dùng Spark engine (không phải Trino) để query
- Nếu warehouse có nhiều bảng, script sẽ chạy chậm do query từng bảng một
- `sqlSource` và `abi` chỉ xuất hiện trong tblproperties nếu pipeline đã ghi chúng vào
- Nếu tblproperties không có `sqlSource`/`abi`, file markdown sẽ không có section SQL Transform/ABI

## Ví dụ thực tế
Script được tạo ra theo yêu cầu build catalog warehouse lần đầu.
