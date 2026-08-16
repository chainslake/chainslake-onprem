import argparse
import sys
from metabase_query import exe_query


def check_table_properties(table_name):
    """
    Check the tblproperties of a table in the Data Warehouse.

    Displays the important properties:
    - isLock: Lock status (1=locked, 0=unlocked)
    - frequenceType: Frequency type (block, hour, minute, day)
    - fromBlock, toBlock: Block range (if frequenceType=block)
    - fromEpochSecond, toEpochSecond: Epoch range (if frequenceType is minute/hour/day)
    """
    sql = f"SHOW TBLPROPERTIES {table_name}"

    try:
        result = exe_query(sql, engine='spark')
    except Exception as e:
        print(f"Error querying tblproperties: {e}")
        sys.exit(1)

    if not result or not result.get('rows'):
        print(f"No properties found for table '{table_name}'.")
        sys.exit(1)

    # Parse the result: each row is [key, value]
    props = {}
    for row in result['rows']:
        key = row[0] if len(row) > 0 else None
        value = row[1] if len(row) > 1 else None
        if key:
            props[key] = value

    if not props:
        print(f"Table '{table_name}' has no properties.")
        sys.exit(0)

    # Display all properties
    print(f"=== tblproperties of '{table_name}' ===\n")
    print(f"{'Property':<30} {'Value':<50}")
    print("-" * 80)
    for key, value in props.items():
        print(f"{key:<30} {str(value):<50}")

    # Highlight important properties
    important_keys = [
        'isLock', 'frequenceType',
        'fromBlock', 'toBlock',
        'fromEpochSecond', 'toEpochSecond'
    ]
    found_important = {k: v for k, v in props.items() if k in important_keys}

    if found_important:
        print(f"\n=== Important properties ===\n")
        for key, value in found_important.items():
            label = key
            if key == 'isLock':
                status = "LOCKED" if str(value) == '1' else "UNLOCKED"
                label = f"{key} ({status})"
            print(f"  {label}: {value}")

    return props


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check the tblproperties of a table in the Data Warehouse"
    )
    parser.add_argument("table", help="Table name (e.g. ethereum.blocks)")
    args = parser.parse_args()

    check_table_properties(args.table)
