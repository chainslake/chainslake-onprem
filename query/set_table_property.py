"""
Set table properties (ALTER TABLE ... SET TBLPROPERTIES) for testing.

ONLY allows setting properties on tables with `_dev` suffix — protects production tables.

Usage:
    # Set properties via SQL
    python query/set_table_property.py "ALTER TABLE ethereum.transactions_dev SET TBLPROPERTIES (fromBlock=1000)"

    # Read SQL from file
    python query/set_table_property.py -f set_props.sql
"""
import argparse
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from metabase_query import exe_query


def extract_target_table(sql):
    """Extract target table name from ALTER TABLE ... SET TBLPROPERTIES statement.

    Returns table name or None if no match.
    """
    m = re.match(
        r"^\s*ALTER\s+TABLE\s+([`\"\w.]+\.[`\"\w]+|[`\"\w]+)\s+SET\s+TBLPROPERTIES",
        sql,
        re.IGNORECASE,
    )
    if not m:
        return None
    return m.group(1).strip('`"')


def check_target_is_dev(sql):
    """Check if the target table in ALTER statement has _dev suffix.

    Returns (ok, message).
    """
    table = extract_target_table(sql)
    if table is None:
        return False, "Statement is not ALTER TABLE ... SET TBLPROPERTIES."

    table_short = table.rsplit('.', 1)[-1]
    if not table_short.endswith('_dev'):
        return False, (
            f"Target table '{table}' does not have _dev suffix. "
            "Only _dev tables are allowed to set properties to protect production."
        )
    return True, table


def block_other_statements(sql):
    """Block statements other than SET TBLPROPERTIES in SQL.

    Returns (ok, keyword) — keyword is the blocked command or None.
    """
    # Only allow a single ALTER ... SET TBLPROPERTIES statement
    rest = re.sub(
        r"^\s*ALTER\s+TABLE\s+[`\"\w.]+\s+SET\s+TBLPROPERTIES",
        "",
        sql,
        count=1,
        flags=re.IGNORECASE,
    )
    for kw in (r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b',
               r'\bTRUNCATE\b', r'\bCREATE\b', r'\bREPLACE\b', r'\bMERGE\b',
               r'\bALTER\b'):
        if re.search(kw, rest, re.IGNORECASE):
            return True, kw.replace(r'\b', '').replace('\\b', '')
    return False, None


def set_table_property(sql, engine='spark'):
    """Execute ALTER TABLE ... SET TBLPROPERTIES and print result."""
    sql = sql.strip()
    if not sql:
        print("Error: Empty SQL")
        sys.exit(1)

    # Check target table has _dev suffix
    ok, info = check_target_is_dev(sql)
    if not ok:
        print(f"Error: {info}")
        sys.exit(1)
    target_table = info

    # Block other statements in SQL
    is_blocked, keyword = block_other_statements(sql)
    if is_blocked:
        print(f"Error: Statement contains '{keyword}' and is blocked.")
        print("Only a single ALTER TABLE ... SET TBLPROPERTIES on _dev tables is allowed.")
        sys.exit(1)

    print(f"SQL:\n{sql}\n")
    try:
        result = exe_query(sql, engine=engine)
        print(f"Success! Properties set for _dev table '{target_table}'.")
        if result and result.get('rows'):
            for row in result['rows']:
                print(row)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Set TBLPROPERTIES for _dev tables (ONLY accepts tables with _dev suffix)"
    )
    parser.add_argument("sql", nargs='?', help="ALTER SQL statement (or '-' to read from stdin)")
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

    set_table_property(sql, engine=args.engine)
