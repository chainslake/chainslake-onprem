"""
Shallow clone bảng Delta Lake — tạo bản copy _dev cho phát triển.

Delta Lake SHALLOW CLONE: chỉ copy metadata, KHÔNG copy data → instant, nhẹ storage.

Usage:
    # Shallow clone (khuyến nghị — instant, không copy data)
    python query/shallow_clone.py ethereum.transactions

    # Shallow clone với tên custom
    python query/shallow_clone.py ethereum.transactions --target ethereum.transactions_dev

    # Clone + copy N dòng (dùng CTAS — chậm hơn, có copy data)
    python query/shallow_clone.py ethereum.transactions --limit 10000
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from metabase_query import exe_query


def shallow_clone(source_table, target_table=None, limit=None, engine='spark'):
    """
    Tạo bản shallow clone của bảng Delta Lake.

    - Không có --limit: dùng Delta SHALLOW CLONE (instant, metadata only)
    - Có --limit: dùng CREATE TABLE AS SELECT ... LIMIT (copy data)
    """
    # Xác định target table
    if target_table is None:
        parts = source_table.rsplit('.', 1)
        if len(parts) == 2:
            target_table = f"{parts[0]}.{parts[1]}_dev"
        else:
            target_table = f"{source_table}_dev"

    # Kiểm tra source table tồn tại
    try:
        exe_query(f"SELECT 1 FROM {source_table} LIMIT 1", engine=engine)
    except Exception:
        print(f"Lỗi: Bảng nguồn '{source_table}' không tồn tại hoặc không truy cập được.")
        sys.exit(1)

    # Lấy schema để hiển thị
    try:
        desc = exe_query(f"DESCRIBE TABLE {source_table}", engine=engine)
        col_count = len(desc['rows']) if desc and desc.get('rows') else '?'
    except Exception:
        col_count = '?'

    # Xác định chế độ
    if limit:
        mode = f"CTAS + LIMIT {limit}"
        sql = f"CREATE TABLE {target_table} AS SELECT * FROM {source_table} LIMIT {limit}"
    else:
        mode = "Delta SHALLOW CLONE (metadata only)"
        sql = f"CREATE TABLE {target_table} SHALLOW CLONE {source_table}"

    # Hiển thị thông tin
    print(f"=== Shallow Clone ===")
    print(f"  Source:  {source_table}")
    print(f"  Target:  {target_table}")
    print(f"  Columns: {col_count}")
    print(f"  Mode:    {mode}")

    # Kiểm tra target đã tồn tại chưa
    try:
        exe_query(f"SELECT 1 FROM {target_table} LIMIT 1", engine=engine)
        print(f"\nCảnh báo: Bảng '{target_table}' đã tồn tại và sẽ bị GHI ĐÈ.")
    except Exception:
        pass

    # Thực thi
    print(f"\nĐang thực thi...")
    try:
        exe_query(sql, engine=engine)
    except Exception as e:
        print(f"Lỗi khi clone bảng: {e}")
        sys.exit(1)

    # Verify
    try:
        result = exe_query(f"SELECT count(*) as total FROM {target_table}", engine=engine)
        total = result['rows'][0][0] if result and result.get('rows') else '?'
        print(f"Thành công! Bảng '{target_table}' đã được tạo với {total} dòng.")
    except Exception:
        print(f"Thành công! Bảng '{target_table}' đã được tạo.")

    # Hiển thị tblproperties quan trọng từ source
    try:
        props = exe_query(f"SHOW TBLPROPERTIES {source_table}", engine=engine)
        if props and props.get('rows'):
            important = {}
            for row in props['rows']:
                if row[0] in ('frequenceType', 'fromBlock', 'toBlock', 'fromEpochSecond', 'toEpochSecond'):
                    important[row[0]] = row[1]
            if important:
                print(f"\nTblproperties từ source (cần set lại cho target nếu cần):")
                for k, v in important.items():
                    print(f"  {k} = {v}")
    except Exception:
        pass

    return target_table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Shallow clone bảng Delta Lake (metadata only, instant)"
    )
    parser.add_argument("source", help="Bảng nguồn (ví dụ: ethereum.transactions)")
    parser.add_argument("--target", help="Bảng đích (mặc định: thêm _dev suffix)")
    parser.add_argument("--limit", type=int, help="Số dòng tối đa (dùng CTAS thay vì SHALLOW CLONE)")
    parser.add_argument("--engine", choices=["spark", "trino"], default="spark")
    args = parser.parse_args()

    shallow_clone(
        source_table=args.source,
        target_table=args.target,
        limit=args.limit,
        engine=args.engine,
    )
