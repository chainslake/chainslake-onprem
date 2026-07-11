"""
Tool thực thi DDL (CREATE SCHEMA, CREATE TABLE, ALTER, DROP...) qua Metabase API với Spark engine.

Usage:
    python query/ddl_spark.py "CREATE SCHEMA IF NOT EXISTS ext_upload"
    python query/ddl_spark.py -f create_table.sql
    echo "CREATE SCHEMA ext_upload" | python query/ddl_spark.py -
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from metabase_query import exe_query


def run_ddl(sql, engine='spark'):
    """Thực thi câu DDL và in kết quả."""
    sql = sql.strip()
    if not sql:
        print("Lỗi: SQL rỗng")
        sys.exit(1)

    print(f"SQL:\n{sql}\n")
    try:
        result = exe_query(sql, engine=engine)
        print("Thành công!")
        if result and result.get('rows'):
            for row in result['rows']:
                print(row)
    except Exception as e:
        print(f"Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Thực thi DDL qua Metabase API (Spark engine)"
    )
    parser.add_argument("sql", nargs='?', help="Câu DDL SQL (hoặc '-' để đọc từ stdin)")
    parser.add_argument("-f", "--file", help="Đọc SQL từ file")
    parser.add_argument("--engine", choices=["spark", "trino"], default="spark")
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r') as f:
            sql = f.read()
    elif args.sql == '-':
        sql = sys.stdin.read()
    elif args.sql:
        sql = args.sql
    else:
        parser.print_help()
        sys.exit(1)

    run_ddl(sql, engine=args.engine)
