"""
Shallow clone a Delta Lake table — create a _dev copy for development.

Delta Lake SHALLOW CLONE: copies metadata only, NO data copy → instant, lightweight.

Usage:
    # Shallow clone (recommended — instant, no data copy)
    python query/shallow_clone.py ethereum.transactions

    # Shallow clone with custom target name
    python query/shallow_clone.py ethereum.transactions --target ethereum.transactions_dev

    # Clone + copy N rows (uses CTAS — slower, copies data)
    python query/shallow_clone.py ethereum.transactions --limit 10000
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from metabase_query import exe_query


def shallow_clone(source_table, target_table=None, limit=None, engine='spark'):
    """
    Create a shallow clone of a Delta Lake table.

    - Without --limit: uses Delta SHALLOW CLONE (instant, metadata only)
    - With --limit: uses CREATE TABLE AS SELECT ... LIMIT (copies data)
    """
    # Determine target table
    if target_table is None:
        parts = source_table.rsplit('.', 1)
        if len(parts) == 2:
            target_table = f"{parts[0]}.{parts[1]}_dev"
        else:
            target_table = f"{source_table}_dev"

    # Check source table exists
    try:
        exe_query(f"SELECT 1 FROM {source_table} LIMIT 1", engine=engine)
    except Exception:
        print(f"Error: Source table '{source_table}' does not exist or is not accessible.")
        sys.exit(1)

    # Get schema for display
    try:
        desc = exe_query(f"DESCRIBE TABLE {source_table}", engine=engine)
        col_count = len(desc['rows']) if desc and desc.get('rows') else '?'
    except Exception:
        col_count = '?'

    # Determine mode
    if limit:
        mode = f"CTAS + LIMIT {limit}"
        sql = f"CREATE TABLE {target_table} AS SELECT * FROM {source_table} LIMIT {limit}"
    else:
        mode = "Delta SHALLOW CLONE (metadata only)"
        sql = f"CREATE TABLE {target_table} SHALLOW CLONE {source_table}"

    # Display info
    print(f"=== Shallow Clone ===")
    print(f"  Source:  {source_table}")
    print(f"  Target:  {target_table}")
    print(f"  Columns: {col_count}")
    print(f"  Mode:    {mode}")

    # Check if target already exists
    try:
        exe_query(f"SELECT 1 FROM {target_table} LIMIT 1", engine=engine)
        print(f"\nWarning: Table '{target_table}' already exists and will be OVERWRITTEN.")
    except Exception:
        pass

    # Execute
    print(f"\nExecuting...")
    try:
        exe_query(sql, engine=engine)
    except Exception as e:
        print(f"Error cloning table: {e}")
        sys.exit(1)

    # Verify
    try:
        result = exe_query(f"SELECT count(*) as total FROM {target_table}", engine=engine)
        total = result['rows'][0][0] if result and result.get('rows') else '?'
        print(f"Success! Table '{target_table}' created with {total} rows.")
    except Exception:
        print(f"Success! Table '{target_table}' created.")

    # Show important tblproperties from source
    try:
        props = exe_query(f"SHOW TBLPROPERTIES {source_table}", engine=engine)
        if props and props.get('rows'):
            important = {}
            for row in props['rows']:
                if row[0] in ('frequenceType', 'fromBlock', 'toBlock', 'fromEpochSecond', 'toEpochSecond'):
                    important[row[0]] = row[1]
            if important:
                print(f"\nTblproperties from source (may need to be re-set for target):")
                for k, v in important.items():
                    print(f"  {k} = {v}")
    except Exception:
        pass

    return target_table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Shallow clone a Delta Lake table (metadata only, instant)"
    )
    parser.add_argument("source", help="Source table (e.g.: ethereum.transactions)")
    parser.add_argument("--target", help="Target table (default: append _dev suffix)")
    parser.add_argument("--limit", type=int, help="Max rows (uses CTAS instead of SHALLOW CLONE)")
    parser.add_argument("--engine", choices=["spark", "trino"], default="spark")
    args = parser.parse_args()

    shallow_clone(
        source_table=args.source,
        target_table=args.target,
        limit=args.limit,
        engine=args.engine,
    )
