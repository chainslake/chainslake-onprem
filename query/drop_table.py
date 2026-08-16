import argparse
from metabase_query import exe_query


def drop_table(table, engine='spark'):
    confirm = input(f"Are you sure you want to drop table '{table}'? Type the table name to confirm: ").strip()
    if confirm != table:
        print("Confirmation does not match. Table drop operation cancelled.")
        return None

    return exe_query(f"DROP TABLE IF EXISTS {table}", engine=engine)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drop a table in the data warehouse")
    parser.add_argument("table", help="Name of the table to drop")
    parser.add_argument("--engine", choices=["spark", "trino"], default="spark", help="Query engine (default: spark)")
    args = parser.parse_args()

    result = drop_table(args.table, engine=args.engine)
    if result is not None:
        print(f"Table '{args.table}' dropped successfully.")
        print(result)
