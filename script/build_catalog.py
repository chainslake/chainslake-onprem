"""
Xây dựng tài liệu catalog cho tất cả bảng trong Data Warehouse.

Thu thập metadata từ warehouse (tblproperties, describe detail, count, schema)
và sinh ra file markdown per-table cùng lineage.md.

Usage:
    python script/build_catalog.py
    python script/build_catalog.py --output-dir /path/to/catalog
    python script/build_catalog.py --skip-count   # Bỏ qua đếm rows (nhanh hơn)
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'query'))
from metabase_query import exe_query

SCHEMAS_TO_SKIP = {'default'}


def show_schemas():
    result = exe_query("SHOW SCHEMAS", engine='spark')
    return [row[0] for row in result['rows'] if row[0] not in SCHEMAS_TO_SKIP]


def show_tables(schema):
    result = exe_query(f"SHOW TABLES IN {schema}", engine='spark')
    tables = []
    for row in result['rows']:
        table_name = row[1] if len(row) > 1 else row[0]
        tables.append({
            'schema': schema,
            'table_name': table_name,
            'full_name': f"{schema}.{table_name}",
        })
    return tables


def get_table_properties(full_name):
    try:
        result = exe_query(f"SHOW TBLPROPERTIES {full_name}", engine='spark')
        props = {}
        for row in result['rows']:
            key = row[0] if len(row) > 0 else None
            value = row[1] if len(row) > 1 else None
            if key:
                props[key] = value
        return props
    except Exception as e:
        print(f"  [WARN] SHOW TBLPROPERTIES failed: {e}")
        return {}


def get_table_detail(full_name):
    try:
        result = exe_query(f"DESCRIBE DETAIL {full_name}", engine='spark')
        if result['rows']:
            row = result['rows'][0]
            cols = [c['name'] for c in result['cols']]
            return dict(zip(cols, row))
        return {}
    except Exception as e:
        print(f"  [WARN] DESCRIBE DETAIL failed: {e}")
        return {}


def get_row_count(full_name):
    try:
        result = exe_query(f"SELECT COUNT(*) AS cnt FROM {full_name}", engine='spark')
        if result['rows']:
            return result['rows'][0][0]
        return None
    except Exception as e:
        print(f"  [WARN] COUNT failed: {e}")
        return None


def get_table_schema(full_name):
    try:
        result = exe_query(f"DESCRIBE TABLE {full_name}", engine='spark')
        seen = set()
        columns = []
        for row in result['rows']:
            col_name = row[0]
            col_type = row[1] if len(row) > 1 else ''
            if col_name and not col_name.startswith('#') and col_name not in ('', ' ') and col_name != 'col_name':
                if col_name not in seen:
                    seen.add(col_name)
                    columns.append({'name': col_name, 'type': col_type})
        return columns
    except Exception as e:
        print(f"  [WARN] DESCRIBE TABLE failed: {e}")
        return []


def get_example_data(full_name):
    try:
        result = exe_query(f"SELECT * FROM {full_name} LIMIT 1", engine='spark')
        return result
    except Exception as e:
        print(f"  [WARN] SELECT example failed: {e}")
        return None


def format_size(size_bytes):
    if size_bytes is None:
        return 'N/A'
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def format_datetime(dt_str):
    if not dt_str:
        return 'N/A'
    try:
        return dt_str.replace('T', ' ').split('.')[0]
    except Exception:
        return str(dt_str)


def build_schema_example_table(columns, example_data):
    if not columns:
        return '_Không có thông tin schema_'

    example_values = {}
    if example_data and example_data.get('rows'):
        for i, col in enumerate(example_data['cols']):
            if i < len(example_data['rows'][0]):
                val = example_data['rows'][0][i]
                example_values[col['name']] = str(val) if val is not None else 'NULL'

    header = '| Column | Type | Example |'
    separator = '|---|---|---|'
    lines = [header, separator]
    for col in columns:
        col_name = col['name']
        col_type = col['type']
        ex = example_values.get(col_name, '')
        if len(ex) > 80:
            ex = ex[:77] + '...'
        lines.append(f"| {col_name} | {col_type} | `{ex}` |")
    return '\n'.join(lines)


def transform_sql_source(sql_source):
    if not sql_source:
        return None
    if '===' in sql_source:
        parts = sql_source.split('===')
        sql_body = parts[-1].strip() if len(parts) > 1 else sql_source
    else:
        sql_body = sql_source
    return sql_body.replace('@', '$').replace('[nl]', '\n').replace('`', "'")


def build_table_markdown(table_info, downstream_map=None):
    schema = table_info['schema']
    table_name = table_info['table_name']
    full_name = table_info['full_name']
    props = table_info.get('properties', {})
    detail = table_info.get('detail', {})
    row_count = table_info.get('row_count')
    columns = table_info.get('columns', [])
    example_data = table_info.get('example_data')

    created_at = format_datetime(detail.get('createdAt'))
    updated_at = format_datetime(detail.get('lastModified'))
    size_bytes = detail.get('sizeInBytes')
    num_files = detail.get('numFiles')

    frequent_type = props.get('frequentType', props.get('frequenceType', 'N/A'))
    from_block = props.get('fromBlock', 'N/A')
    to_block = props.get('toBlock', 'N/A')
    from_epoch = props.get('fromEpochSecond', 'N/A')
    to_epoch = props.get('toEpochSecond', 'N/A')
    list_input = props.get('listInputTables', '')
    sql_source = props.get('sqlSource', None)
    abi = props.get('abi', None)

    parts = []
    parts.append(f"# {full_name}\n")

    # Trang thai
    parts.append("## Trạng thái\n")
    parts.append("| Thuộc tính | Giá trị |")
    parts.append("|---|---|")
    parts.append(f"| Ngày tạo | {created_at} |")
    parts.append(f"| Ngày update gần nhất | {updated_at} |")
    parts.append(f"| Số bản ghi | {row_count if row_count is not None else 'N/A'} |")
    parts.append(f"| Số file | {num_files if num_files is not None else 'N/A'} |")
    parts.append(f"| Dung lượng | {format_size(size_bytes)} |")
    parts.append(f"| frequentType | {frequent_type} |")
    parts.append(f"| fromBlock | {from_block} |")
    parts.append(f"| toBlock | {to_block} |")
    parts.append(f"| fromEpochSecond | {from_epoch} |")
    parts.append(f"| toEpochSecond | {to_epoch} |")
    parts.append("")

    # Lineage
    upstreams = [t.strip() for t in list_input.split(',') if t.strip()] if list_input else []
    upstreams = [u for u in upstreams if u not in NON_TABLE_UPSTREAMS]
    downs = downstream_map.get(full_name, []) if downstream_map else []
    parts.append("## Lineage\n")
    if upstreams:
        parts.append(f"- **Upstream tables**: {', '.join(upstreams)}")
    else:
        parts.append("- **Upstream tables**: _RPC Node (Blockchain)_")
    if downs:
        parts.append(f"- **Downstream tables**: {', '.join(downs)}")
    else:
        parts.append("- **Downstream tables**: _None_")
    parts.append("")

    # Schema + Example
    parts.append("## Schema\n")
    parts.append(build_schema_example_table(columns, example_data))
    parts.append("")

    # SQL Transform
    sql_body = transform_sql_source(sql_source)
    if sql_body:
        parts.append("## SQL Transform\n")
        parts.append("```sql")
        parts.append(sql_body)
        parts.append("```\n")

    # ABI
    if abi:
        parts.append("## ABI\n")
        parts.append(render_abi(abi))
        parts.append("")

    return '\n'.join(parts)


NON_TABLE_UPSTREAMS = {'node'}


def render_abi(abi_str):
    import json
    try:
        abi_data = json.loads(abi_str)
    except (json.JSONDecodeError, TypeError):
        return f"```json\n{abi_str}\n```\n"

    lines = []
    for abi_name, abi_items in abi_data.items():
        if not isinstance(abi_items, list):
            continue
        lines.append(f"### {abi_name}\n")
        for item in abi_items:
            item_type = item.get('type', 'unknown')
            item_name = item.get('name', 'unnamed')

            if item_type == 'event':
                inputs = item.get('inputs', [])
                params = ', '.join(
                    f"{'indexed ' if inp.get('indexed') else ''}{inp['type']} {inp['name']}"
                    for inp in inputs
                )
                lines.append(f"#### `{item_name}({params})` — event\n")
            elif item_type == 'function':
                inputs = item.get('inputs', [])
                outputs = item.get('outputs', [])
                in_params = ', '.join(f"{inp['type']} {inp['name']}" for inp in inputs)
                out_params = ', '.join(f"{out['type']}" for out in outputs)
                mutability = item.get('stateMutability', '')
                sig = f"{item_name}({in_params})"
                if out_params:
                    sig += f" returns ({out_params})"
                lines.append(f"#### `{sig}` — {mutability} function\n")

            lines.append("```json")
            lines.append(json.dumps(item, indent=2))
            lines.append("```\n")

    return '\n'.join(lines) if lines else f"```json\n{abi_str}\n```\n"


def build_lineage_md(all_tables):
    upstream_map = {}
    for t in all_tables:
        full_name = t['full_name']
        props = t.get('properties', {})
        list_input = props.get('listInputTables', '')
        upstreams = [x.strip() for x in list_input.split(',') if x.strip()] if list_input else []
        upstreams = [u for u in upstreams if u not in NON_TABLE_UPSTREAMS]
        upstream_map[full_name] = upstreams

    downstream_map = {name: [] for name in upstream_map}
    for table_name, upstreams in upstream_map.items():
        for up in upstreams:
            if up in downstream_map:
                downstream_map[up].append(table_name)

    all_names = sorted(upstream_map.keys())
    node_id = {}
    for i, name in enumerate(all_names):
        node_id[name] = f"T{i}"

    has_rpc = any(
        'node' in (t.get('properties', {}).get('listInputTables', '') or '')
        for t in all_tables
    )

    lines = ["# Data Warehouse Lineage\n"]
    lines.append("Biểu đồ thể hiện sự phụ thuộc (lineage) giữa các bảng trong warehouse.")
    lines.append("Mũi tên `-->` nghĩa là \"được sử dụng để tạo ra\".\n")

    lines.append("## Mermaid Graph\n")
    lines.append("```mermaid")
    lines.append("graph LR")

    if has_rpc:
        lines.append('    RPC["RPC Node (Blockchain)"]')

    for name in all_names:
        nid = node_id[name]
        short = name
        lines.append(f"    {nid}[\"{short}\"]")

    if has_rpc:
        for t in all_tables:
            list_input = t.get('properties', {}).get('listInputTables', '')
            if 'node' in (list_input or ''):
                lines.append(f"    RPC --> {node_id[t['full_name']]}")

    for name in all_names:
        for up in upstream_map[name]:
            if up in node_id:
                lines.append(f"    {node_id[up]} --> {node_id[name]}")

    lines.append("```\n")

    lines.append("## Bảng chi tiết\n")
    lines.append("| Bảng | Upstream | Downstream |")
    lines.append("|---|---|---|")
    for name in all_names:
        ups = upstream_map[name]
        downs = downstream_map[name]
        up_str = ', '.join(ups) if ups else '_none_ (RPC Node)_'
        down_str = ', '.join(downs) if downs else '_none_'
        lines.append(f"| `{name}` | {up_str} | {down_str} |")

    lines.append("")

    root_tables = [n for n in all_names if not upstream_map[n]]
    leaf_tables = [n for n in all_names if not downstream_map[n]]

    if root_tables:
        lines.append("## Root tables (không có upstream)\n")
        for t in root_tables:
            lines.append(f"- `{t}`")
        lines.append("")

    if leaf_tables:
        lines.append("## Leaf tables (không có downstream)\n")
        for t in leaf_tables:
            lines.append(f"- `{t}`")
        lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="Xây dựng catalog data warehouse")
    parser.add_argument("--output-dir", default="catalog", help="Thư mục output (default: catalog)")
    parser.add_argument("--skip-count", action="store_true", help="Bỏ qua đếm số rows")
    parser.add_argument("--skip-example", action="store_true", help="Bỏ qua lấy ví dụ dữ liệu")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, args.output_dir)

    os.makedirs(output_dir, exist_ok=True)
    print(f"Output: {output_dir}\n")

    # Step 1: Get all schemas
    print("=== Đang lấy danh sách schemas ===")
    schemas = show_schemas()
    print(f"Tìm thấy {len(schemas)} schemas: {', '.join(schemas)}\n")

    # Step 2: Get all tables
    all_tables = []
    for schema in schemas:
        print(f"--- Schema: {schema} ---")
        tables = show_tables(schema)
        print(f"  Tìm thấy {len(tables)} bảng")
        all_tables.extend(tables)
        print()

    print(f"Tổng cộng: {len(all_tables)} bảng\n")

    # Step 3: Gather metadata for each table
    print("=== Đang thu thập metadata ===\n")
    for i, table in enumerate(all_tables):
        full_name = table['full_name']
        print(f"[{i + 1}/{len(all_tables)}] {full_name}")

        print(f"  [1/5] TBLPROPERTIES...")
        table['properties'] = get_table_properties(full_name)

        print(f"  [2/5] DESCRIBE DETAIL...")
        table['detail'] = get_table_detail(full_name)

        if not args.skip_count:
            print(f"  [3/5] COUNT(*)...")
            table['row_count'] = get_row_count(full_name)
        else:
            table['row_count'] = None

        print(f"  [4/5] DESCRIBE TABLE...")
        table['columns'] = get_table_schema(full_name)

        if not args.skip_example:
            print(f"  [5/5] SELECT example...")
            table['example_data'] = get_example_data(full_name)
        else:
            table['example_data'] = None

        props = table.get('properties', {})
        row_count = table.get('row_count', 'N/A')
        num_files = table.get('detail', {}).get('numFiles', 'N/A')
        print(f"  => rows={row_count}, files={num_files}, props={list(props.keys())}\n")

    # Step 4: Build downstream map
    downstream_map = {t['full_name']: [] for t in all_tables}
    for t in all_tables:
        list_input = t.get('properties', {}).get('listInputTables', '')
        upstreams = [x.strip() for x in list_input.split(',') if x.strip()] if list_input else []
        upstreams = [u for u in upstreams if u not in NON_TABLE_UPSTREAMS]
        for up in upstreams:
            if up in downstream_map:
                downstream_map[up].append(t['full_name'])

    # Step 5: Generate per-table markdown
    print("=== Đang tạo file markdown ===\n")
    for table in all_tables:
        md_content = build_table_markdown(table, downstream_map)
        filename = f"{table['full_name']}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  Da tao: {filename}")

    # Step 6: Generate lineage.md
    print(f"\n=== Dong lineage.md ===")
    lineage_content = build_lineage_md(all_tables)
    lineage_path = os.path.join(output_dir, "lineage.md")
    with open(lineage_path, 'w', encoding='utf-8') as f:
        f.write(lineage_content)
    print(f"  Da tao: lineage.md")

    print(f"\n=== Hoan tat! ===")
    print(f"Tong so file: {len(all_tables) + 1}")
    print(f"Thu muc output: {output_dir}")


if __name__ == "__main__":
    main()
