"""
Tool to execute DDL (CREATE SCHEMA, CREATE TABLE, ALTER, DROP...) via Metabase API with Spark engine.

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
    """Execute DDL statement and print result."""
    sql = sql.strip()
    if not sql:
        print("Error: Empty SQL")
        sys.exit(1)

    print(f"SQL:\n{sql}\n")
    try:
        result = exe_query(sql, engine=engine)
        print("Success!")
        if result and result.get('rows'):
            for row in result['rows']:
                print(row)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Execute DDL via Metabase API (Spark engine)"
    )
    parser.add_argument("sql", nargs='?', help="DDL SQL statement (or '-' to read from stdin)")
    parser.add_argument("-f", "--file", help="Read SQL from file")
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
