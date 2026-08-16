import argparse
import sys
from metabase_query import exe_query


def unlock_table(table_name):
    """
    Unlock a table in the Data Warehouse by setting isLock=0.

    Use when a data-writing job fails with the "Table is Lock" error.
    ONLY use when you are certain no job is currently writing to the table.
    """
    sql = f"ALTER TABLE {table_name} SET TBLPROPERTIES (isLock=0)"

    # Confirm before proceeding
    print(f"⚠️  You are about to unlock table '{table_name}'.")
    print(f"    Command to be executed: {sql}")
    print()
    confirm = input(f"Type the table name to confirm: ").strip()

    if confirm != table_name:
        print("Confirmation does not match. Operation cancelled.")
        sys.exit(0)

    try:
        exe_query(sql, engine='spark')
        print(f"\n✅ Table '{table_name}' unlocked successfully.")
    except Exception as e:
        print(f"\n❌ Error unlocking the table: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Unlock a table in the Data Warehouse (set isLock=0)"
    )
    parser.add_argument("table", help="Name of the table to unlock (e.g. ethereum.blocks)")
    args = parser.parse_args()

    unlock_table(args.table)
