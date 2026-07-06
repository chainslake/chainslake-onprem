import argparse
from metabase_query import exe_query

def get_example_table(table):
    return exe_query(f"select * from {table} limit 1")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lấy 1 bản ghi mẫu từ bảng trong datawarehouse qua Metabase")
    parser.add_argument("table", help="Tên bảng, ví dụ: ethereum.transactions")
    args = parser.parse_args()

    result = get_example_table(args.table)
    print(result)