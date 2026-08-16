"""
Insert data vào bảng _dev để phục vụ testing.

CHỈ cho phép insert vào bảng có hậu tố `_dev` — bảo vệ production tables.
Nếu INSERT dạng SELECT thì bắt buộc có mệnh đề LIMIT.

Usage:
    # Insert theo VALUES
    python query/insert_dev_data.py "INSERT INTO ethereum.transactions_dev (hash, block_number) VALUES ('0xabc', 123)"

    # Insert từ câu SELECT (bắt buộc có LIMIT)
    python query/insert_dev_data.py "INSERT INTO ethereum.transactions_dev SELECT * FROM ethereum.transactions_dev LIMIT 10"

    # Insert Overwrite (bắt buộc có LIMIT nếu dùng SELECT)
    python query/insert_dev_data.py "INSERT OVERWRITE ethereum.transactions_dev SELECT * FROM ethereum.transactions_dev LIMIT 10"

    # Đọc SQL từ file
    python query/insert_dev_data.py -f insert.sql
"""
import argparse
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from metabase_query import exe_query


def extract_target_table(sql):
    """Trích xuất tên bảng đích từ câu INSERT.

    Hỗ trợ: INSERT INTO <table> ... / INSERT OVERWRITE <table> ...
    Trả về (table_name, keyword) hoặc (None, None) nếu không phải INSERT.
    """
    m = re.match(
        r"^\s*INSERT\s+(?:OVERWRITE\s+)?INTO\s+([`\"\w.]+\.[`\"\w]+|[`\"\w]+)",
        sql,
        re.IGNORECASE,
    )
    if not m:
        # Cũng hỗ trợ INSERT OVERWRITE <table> ... (không có INTO)
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
    """Kiểm tra bảng đích trong câu INSERT có hậu tố _dev hay không.

    Trả về (ok, message).
    """
    table, _ = extract_target_table(sql)
    if table is None:
        return False, "Câu lệnh không phải INSERT INTO/INSERT OVERWRITE."

    # Lấy phần tên bảng cuối cùng (sau dấu .)
    table_short = table.rsplit('.', 1)[-1]
    if not table_short.endswith('_dev'):
        return False, (
            f"Bảng đích '{table}' không có hậu tố _dev. "
            "CHỈ cho phép insert vào bảng _dev để bảo vệ production."
        )
    return True, table


def check_requires_limit(sql):
    """Kiểm tra câu INSERT dạng SELECT bắt buộc có LIMIT.

    - INSERT ... SELECT ... → bắt buộc có LIMIT (chống insert số lượng lớn).
    - INSERT ... VALUES ... → không cần (VALUES không hợp lệ với LIMIT).

    Trả về (ok, message).
    """
    sql_upper = sql.upper()

    # Tách phần sau INSERT INTO <table> — nơi chứa SELECT/VALUES
    rest = re.sub(
        r"^\s*INSERT\s+(?:OVERWRITE\s+)?(?:INTO\s+)?[`\"\w.]+\s*",
        "",
        sql,
        count=1,
        flags=re.IGNORECASE,
    )

    has_select = re.search(r"\bSELECT\b", rest, re.IGNORECASE)
    if not has_select:
        return True, None  # VALUES — không yêu cầu LIMIT

    if not re.search(r"\bLIMIT\s+\d+", sql_upper):
        return False, "Câu INSERT dạng SELECT phải có mệnh đề LIMIT để giới hạn số bản ghi."
    return True, None


def block_other_destructive(sql):
    """Chặn các lệnh destructive khác trong câu SQL (UPDATE/DELETE/DROP/TRUNCATE/ALTER/CREATE).

    Lưu ý: INSERT là mục đích của tool nên không bị chặn.
    """
    # Bỏ phần INSERT đầu câu để không vô tình khớp với chính INSERT
    rest = re.sub(r"^\s*INSERT\s+(?:OVERWRITE\s+)?(?:INTO\s+)?[`\"\w.]+\s*", "", sql, count=1, flags=re.IGNORECASE)
    for kw in (r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b', r'\bTRUNCATE\b',
               r'\bALTER\b', r'\bCREATE\b', r'\bREPLACE\b', r'\bMERGE\b'):
        if re.search(kw, rest, re.IGNORECASE):
            return True, kw.replace(r'\b', '').replace('\\b', '')
    return False, None


def insert_dev_data(sql, engine='spark'):
    """Thực thi câu INSERT và in kết quả."""
    sql = sql.strip()
    if not sql:
        print("Lỗi: SQL rỗng")
        sys.exit(1)

    # Kiểm tra bảng đích phải có _dev
    ok, info = check_target_is_dev(sql)
    if not ok:
        print(f"Lỗi: {info}")
        sys.exit(1)
    target_table = info

    # Kiểm tra INSERT dạng SELECT bắt buộc có LIMIT
    ok, limit_msg = check_requires_limit(sql)
    if not ok:
        print(f"Lỗi: {limit_msg}")
        sys.exit(1)

    # Chặn lệnh destructive khác trong SQL
    is_destructive, keyword = block_other_destructive(sql)
    if is_destructive:
        print(f"Lỗi: Câu lệnh chứa lệnh '{keyword}' có thể thay đổi dữ liệu và bị chặn.")
        print("Chỉ cho phép INSERT vào bảng _dev.")
        sys.exit(1)

    print(f"SQL:\n{sql}\n")
    try:
        result = exe_query(sql, engine=engine)
        print(f"Thành công! Đã insert vào bảng _dev '{target_table}'.")
        if result and result.get('rows'):
            for row in result['rows']:
                print(row)
    except Exception as e:
        print(f"Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Insert data vào bảng _dev (CHỈ chấp nhận bảng có hậu tố _dev)"
    )
    parser.add_argument("sql", nargs='?', help="Câu INSERT SQL (hoặc '-' để đọc từ stdin)")
    parser.add_argument("-f", "--file", help="Đọc SQL từ file")
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
