"""
Insert data into _dev tables for testing.

ONLY allows insert into tables with `_dev` suffix — protects production tables.
INSERT with SELECT requires a LIMIT clause.

Usage:
    # Insert via VALUES
    python query/insert_dev_data.py "INSERT INTO ethereum.transactions_dev (hash, block_number) VALUES ('0xabc', 123)"

    # Insert from SELECT (LIMIT required)
    python query/insert_dev_data.py "INSERT INTO ethereum.transactions_dev SELECT * FROM ethereum.transactions_dev LIMIT 10"

    # Insert Overwrite (LIMIT required if using SELECT)
    python query/insert_dev_data.py "INSERT OVERWRITE ethereum.transactions_dev SELECT * FROM ethereum.transactions_dev LIMIT 10"

    # Read SQL from file
    python query/insert_dev_data.py -f insert.sql
"""
import argparse
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from metabase_query import exe_query


def extract_target_table(sql):
    """Extract target table name from INSERT statement.

    Supports: INSERT INTO <table> ... / INSERT OVERWRITE <table> ...
    Returns (table_name, keyword) or (None, None) if not INSERT.
    """
    m = re.match(
        r"^\s*INSERT\s+(?:OVERWRITE\s+)?INTO\s+([`\"\w.]+\.[`\"\w]+|[`\"\w]+)",
        sql,
        re.IGNORECASE,
    )
    if not m:
        # Also support INSERT OVERWRITE <table> ... (without INTO)
        m = re.match(
            r"^\s*INSERT\s+OVERWRITE\s+([`\"\w.]+\.[`\"\w]+|[`\"\w]+)",
            sql,
            re.IGNORECASE,
        )
        if not m:
            return None, None
    table = m.group(1).strip('`"')
    keyword = "INSERT OVERWRITE" if re.match(
        r"^\s*INSERT\s+OVERWRITE\s+INTO", sql, re.IGNORECASE
    ) else "INSERT INTO"
    return table, keyword


def check_target_is_dev(sql):
    """Check if the target table in INSERT statement has _dev suffix.

    Returns (ok, message).
    """
    table, _ = extract_target_table(sql)
    if table is None:
        return False, "Statement is not INSERT INTO/INSERT OVERWRITE."

    # Get the last part of table name (after dot)
    table_short = table.rsplit('.', 1)[-1]
    if not table_short.endswith('_dev'):
        return False, (
            f"Target table '{table}' does not have _dev suffix. "
            "Only inserts into _dev tables are allowed to protect production."
        )
    return True, table


def check_requires_limit(sql):
    """Check if INSERT with SELECT requires LIMIT.

    - INSERT ... SELECT ... → LIMIT required (prevents large inserts).
    - INSERT ... VALUES ... → no LIMIT needed (VALUES cannot use LIMIT).

    Returns (ok, message).
    """
    sql_upper = sql.upper()

    # Extract part after INSERT INTO <table> — contains SELECT/VALUES
    rest = re.sub(
        r"^\s*INSERT\s+(?:OVERWRITE\s+)?(?:INTO\s+)?[`\"\w.]+\s*",
        "",
        sql,
        count=1,
        flags=re.IGNORECASE,
    )

    has_select = re.search(r"\bSELECT\b", rest, re.IGNORECASE)
    if not has_select:
        return True, None  # VALUES — no LIMIT required

    if not re.search(r"\bLIMIT\s+\d+", sql_upper):
        return False, "INSERT with SELECT must have a LIMIT clause to limit the number of records."
    return True, None


def block_other_destructive(sql):
    """Block other destructive statements in SQL (UPDATE/DELETE/DROP/TRUNCATE/ALTER/CREATE).

    Note: INSERT is the purpose of this tool so it is not blocked.
    """
    # Remove the leading INSERT to avoid accidentally matching itself
    rest = re.sub(r"^\s*INSERT\s+(?:OVERWRITE\s+)?(?:INTO\s+)?[`\"\w.]+\s*", "", sql, count=1, flags=re.IGNORECASE)
    for kw in (r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b', r'\bTRUNCATE\b',
               r'\bALTER\b', r'\bCREATE\b', r'\bREPLACE\b', r'\bMERGE\b'):
        if re.search(kw, rest, re.IGNORECASE):
            return True, kw.replace(r'\b', '').replace('\\b', '')
    return False, None


def insert_dev_data(sql, engine='spark'):
    """Execute INSERT statement and print result."""
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

    # Check INSERT with SELECT requires LIMIT
    ok, limit_msg = check_requires_limit(sql)
    if not ok:
        print(f"Error: {limit_msg}")
        sys.exit(1)

    # Block other destructive statements in SQL
    is_destructive, keyword = block_other_destructive(sql)
    if is_destructive:
        print(f"Error: Statement contains '{keyword}' which can modify data and is blocked.")
        print("Only INSERT into _dev tables is allowed.")
        sys.exit(1)

    print(f"SQL:\n{sql}\n")
    try:
        result = exe_query(sql, engine=engine)
        print(f"Success! Inserted into _dev table '{target_table}'.")
        if result and result.get('rows'):
            for row in result['rows']:
                print(row)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Insert data into _dev tables (ONLY accepts tables with _dev suffix)"
    )
    parser.add_argument("sql", nargs='?', help="INSERT SQL statement (or '-' to read from stdin)")
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

    insert_dev_data(sql, engine=args.engine)
