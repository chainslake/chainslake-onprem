import argparse
import sys
from metabase_query import exe_query


def check_table_properties(table_name):
    """
    Kiểm tra tblproperties của bảng trên Data Warehouse.

    Hiển thị các thuộc tính quan trọng:
    - isLock: Trạng thái khóa (1=locked, 0=unlocked)
    - frequenceType: Loại tần suất (block, hour, minute, day)
    - fromBlock, toBlock: Phạm vi block (nếu frequenceType=block)
    - fromEpochSecond, toEpochSecond: Phạm vi epoch (nếu frequenceType là minute/hour/day)
    """
    sql = f"SHOW TBLPROPERTIES {table_name}"

    try:
        result = exe_query(sql, engine='spark')
    except Exception as e:
        print(f"Lỗi khi truy vấn tblproperties: {e}")
        sys.exit(1)

    if not result or not result.get('rows'):
        print(f"Không tìm thấy properties cho bảng '{table_name}'.")
        sys.exit(1)

    # Parse kết quả: mỗi row là [key, value]
    props = {}
    for row in result['rows']:
        key = row[0] if len(row) > 0 else None
        value = row[1] if len(row) > 1 else None
        if key:
            props[key] = value

    if not props:
        print(f"Bảng '{table_name}' không có property nào.")
        sys.exit(0)

    # Hiển thị tất cả properties
    print(f"=== tblproperties của '{table_name}' ===\n")
    print(f"{'Property':<30} {'Value':<50}")
    print("-" * 80)
    for key, value in props.items():
        print(f"{key:<30} {str(value):<50}")

    # Highlight các property quan trọng
    important_keys = [
        'isLock', 'frequenceType',
        'fromBlock', 'toBlock',
        'fromEpochSecond', 'toEpochSecond'
    ]
    found_important = {k: v for k, v in props.items() if k in important_keys}

    if found_important:
        print(f"\n=== Property quan trọng ===\n")
        for key, value in found_important.items():
            label = key
            if key == 'isLock':
                status = "BỊ KHÓA" if str(value) == '1' else "ĐÃ MỞ KHÓA"
                label = f"{key} ({status})"
            print(f"  {label}: {value}")

    return props


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Kiểm tra tblproperties của bảng trên Data Warehouse"
    )
    parser.add_argument("table", help="Tên bảng (ví dụ: ethereum.blocks)")
    args = parser.parse_args()

    check_table_properties(args.table)
