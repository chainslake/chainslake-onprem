import argparse
import sys
from metabase_query import exe_query


def unlock_table(table_name):
    """
    Mở khóa bảng trên Data Warehouse bằng cách set isLock=0.

    Sử dụng khi job ghi dữ liệu bị lỗi "Table is Lock".
    CHỈ sử dụng khi chắc chắn không còn job nào đang ghi vào bảng.
    """
    sql = f"ALTER TABLE {table_name} SET TBLPROPERTIES (isLock=0)"

    # Xác nhận trước khi thực hiện
    print(f"⚠️  Bạn sắp mở khóa bảng '{table_name}'.")
    print(f"    Lệnh sẽ thực thi: {sql}")
    print()
    confirm = input(f"Nhập tên bảng để xác nhận: ").strip()

    if confirm != table_name:
        print("Xác nhận không khớp. Hủy thao tác.")
        sys.exit(0)

    try:
        exe_query(sql, engine='spark')
        print(f"\n✅ Đã mở khóa bảng '{table_name}' thành công.")
    except Exception as e:
        print(f"\n❌ Lỗi khi mở khóa bảng: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mở khóa bảng trên Data Warehouse (set isLock=0)"
    )
    parser.add_argument("table", help="Tên bảng cần mở khóa (ví dụ: ethereum.blocks)")
    args = parser.parse_args()

    unlock_table(args.table)
