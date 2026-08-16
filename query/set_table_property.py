"""
Set properties của bảng (ALTER TABLE ... SET TBLPROPERTIES) để phục vụ testing.

CHỈ cho phép set properties trên bảng có hậu tố `_dev` — bảo vệ production tables.

Usage:
    # Set properties theo SQL
    python query/set_table_property.py "ALTER TABLE ethereum.transactions_dev SET TBLPROPERTIES (fromBlock=1000)"

    # Đọc SQL từ file
    python query/set_table_property.py -f set_props.sql
"""
import argparse
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from metabase_query import exe_query


def extract_target_table(sql):
    """Trích xuất tên bảng đích từ câu ALTER TABLE ... SET TBLPROPERTIES.

    Trả về table name hoặc None nếu không khớp.
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
    """Kiểm tra bảng đích trong câu ALTER có hậu tố _dev hay không.

    Trả về (ok, message).
    """
    table = extract_target_table(sql)
    if table is None:
        return False, "Câu lệnh không phải ALTER TABLE ... SET TBLPROPERTIES."

    table_short = table.rsplit('.', 1)[-1]
    if not table_short.endswith('_dev'):
        return False, (
            f"Bảng đích '{table}' không có hậu tố _dev. "
            "CHỈ cho phép set properties trên bảng _dev để bảo vệ production."
        )
    return True, table


def block_other_statements(sql):
    """Chặn các câu lệnh khác ngoài SET TBLPROPERTIES trong SQL.

    Trả về (ok, keyword) — keyword là lệnh bị chặn hoặc None.
    """
    # Chỉ cho phép một câu ALTER ... SET TBLPROPERTIES duy nhất
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
    """Thực thi câu ALTER TABLE ... SET TBLPROPERTIES và in kết quả."""
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

    # Chặn lệnh khác trong SQL
    is_blocked, keyword = block_other_statements(sql)
    if is_blocked:
        print(f"Lỗi: Câu lệnh chứa lệnh '{keyword}' và bị chặn.")
        print("Chỉ cho phép duy nhất một lệnh ALTER TABLE ... SET TBLPROPERTIES trên bảng _dev.")
        sys.exit(1)

    print(f"SQL:\n{sql}\n")
    try:
        result = exe_query(sql, engine=engine)
        print(f"Thành công! Đã set properties cho bảng _dev '{target_table}'.")
        if result and result.get('rows'):
            for row in result['rows']:
                print(row)
    except Exception as e:
        print(f"Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Set TBLPROPERTIES cho bảng _dev (CHỈ chấp nhận bảng có hậu tố _dev)"
    )
    parser.add_argument("sql", nargs='?', help="Câu ALTER SQL (hoặc '-' để đọc từ stdin)")
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

    set_table_property(sql, engine=args.engine)
