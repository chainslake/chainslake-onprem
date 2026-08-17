import argparse
from metabase_query import exe_query


def run_query(sql, engine='spark'):
    # Check for destructive SQL
    is_destructive, keyword = check_destructive(sql)
    if is_destructive:
        print(f"Error: Query contains '{keyword}' which can modify data and is blocked.")
        print("Only SELECT queries (read-only) are allowed.")
        return None

    # Check LIMIT
    if not check_limit(sql):
        print("Error: Query must have a LIMIT clause to limit the number of records returned.")
        print("Example: SELECT * FROM ethereum.transactions LIMIT 100")
        return None

    return exe_query(sql, engine=engine)


def check_destructive(sql):
    """Check if the query contains data modification statements."""
    import re
    DESTRUCTIVE_KEYWORDS = [
        r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b',
        r'\bTRUNCATE\b', r'\bALTER\b', r'\bCREATE\b', r'\bREPLACE\b', r'\bMERGE\b',
    ]
    sql_upper = sql.upper()
    for pattern in DESTRUCTIVE_KEYWORDS:
        if re.search(pattern, sql_upper):
            keyword = pattern.replace(r'\b', '').replace('\\b', '')
            return True, keyword
    return False, None


def check_limit(sql):
    """Check if the query contains a LIMIT clause."""
    import re
    return bool(re.search(r'\bLIMIT\s+\d+', sql, re.IGNORECASE))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Execute SQL query on datawarehouse via Metabase (SELECT with LIMIT only)"
    )
    parser.add_argument("sql", help="SQL query statement")
    parser.add_argument("--engine", choices=["spark", "trino"], default="spark", help="Query engine (default: spark)")
    args = parser.parse_args()

    result = run_query(args.sql, engine=args.engine)
    if result is not None:
        print(result)
