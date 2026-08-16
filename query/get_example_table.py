import argparse
from metabase_query import exe_query


def get_example_table(table, engine='spark'):
    return exe_query(f"select * from {table} limit 1", engine=engine)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get 1 sample record from a table in the data warehouse")
    parser.add_argument("table", help="Table name, e.g. ethereum.transactions")
    parser.add_argument("--engine", choices=["spark", "trino"], default="spark", help="Query engine (default: spark)")
    args = parser.parse_args()

    result = get_example_table(args.table, engine=args.engine)
    print(result)
