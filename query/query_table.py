import argparse
from metabase_query import exe_query


def run_query(sql, engine='spark'):
    # Kiểm tra destructive SQL
    is_destructive, keyword = check_destructive(sql)
    if is_destructive:
        print(f"Lỗi: Câu truy vấn chứa lệnh '{keyword}' có thể thay đổi dữ liệu và bị chặn.")
        print("Chỉ cho phép các câu truy vấn SELECT (read-only).")
        return None

    # Kiểm tra LIMIT
    if not check_limit(sql):
        print("Lỗi: Câu truy vấn phải có mệnh đề LIMIT để giới hạn số bản ghi trả về.")
        print("Ví dụ: SELECT * FROM ethereum.transactions LIMIT 100")
        return None

    return exe_query(sql, engine=engine)


def check_destructive(sql):
    """Kiểm tra câu truy vấn có chứa các lệnh thay đổi dữ liệu hay không."""
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
    """Kiểm tra câu truy vấn có chứa mệnh đề LIMIT hay không."""
    import re
    return bool(re.search(r'\bLIMIT\s+\d+', sql, re.IGNORECASE))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Thực thi câu truy vấn SQL trên datawarehouse qua Metabase (chỉ SELECT có LIMIT)"
    )
    parser.add_argument("sql", help="Câu truy vấn SQL")
    parser.add_argument("--engine", choices=["spark", "trino"], default="spark", help="Query engine (default: spark)")
    args = parser.parse_args()

    result = run_query(args.sql, engine=args.engine)
    if result is not None:
        print(result)
