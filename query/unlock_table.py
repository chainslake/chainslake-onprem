import argparse
import sys
from metabase_query import exe_query


def unlock_table(table_name):
    """
    Unlock a table on the Data Warehouse by setting isLock=0.

    Use when a job write fails with "Table is Lock" error.
    ONLY use when certain no other job is writing to the table.
    """
    sql = f"ALTER TABLE {table_name} SET TBLPROPERTIES (isLock=0)"

    # Confirm before executing
    print(f"You are about to unlock table '{table_name}'.")
    print(f"    Command to execute: {sql}")
    print()
    confirm = input(f"Enter table name to confirm: ").strip()

    if confirm != table_name:
        print("Confirmation mismatch. Operation cancelled.")
        sys.exit(0)

    try:
        exe_query(sql, engine='spark')
        print(f"\nTable '{table_name}' unlocked successfully.")
    except Exception as e:
        print(f"\nError unlocking table: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Unlock table on Data Warehouse (set isLock=0)"
    )
    parser.add_argument("table", help="Table name to unlock (e.g.: ethereum.blocks)")
    args = parser.parse_args()

    unlock_table(args.table)
