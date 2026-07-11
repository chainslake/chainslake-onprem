import argparse
from metabase_query import exe_query


def drop_table(table, engine='spark'):
    confirm = input(f"Bạn có chắc chắn muốn xóa bảng '{table}'? Nhập tên bảng để xác nhận: ").strip()
    if confirm != table:
        print("Xác nhận không khớp. Hủy thao tác xóa bảng.")
        return None

    return exe_query(f"DROP TABLE IF EXISTS {table}", engine=engine)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xóa một bảng trong datawarehouse")
    parser.add_argument("table", help="Tên bảng cần xóa")
    parser.add_argument("--engine", choices=["spark", "trino"], default="spark", help="Query engine (default: spark)")
    args = parser.parse_args()

    result = drop_table(args.table, engine=args.engine)
    if result is not None:
        print(f"Đã xóa bảng '{args.table}' thành công.")
        print(result)
