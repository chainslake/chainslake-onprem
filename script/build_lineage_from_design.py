#!/usr/bin/env python3
"""
Xây dựng lineage.md từ các file design của Data Architect.

Đọc tất cả file markdown trong thư mục design của một bài toán
(docs/<problem>/design/*.md), trích xuất quan hệ upstream/downstream giữa các
bảng, xác định trạng thái từng bảng (đã có trong warehouse / cần làm mới), và
sinh file lineage.md (Mermaid graph + bảng chi tiết) ngay trong thư mục design —
format tương tự lineage.md của thư mục catalog do build_catalog.py tạo ra.

Nguồn upstream lấy từ row `list_input_tables` trong bảng Header (mục SQL Transform)
của từng file design; downstream được suy ra bằng cách đảo ngược upstream
(giống build_catalog.py). Trạng thái bảng được xác định bằng cách truy vấn
warehouse (Spark), hoặc dùng thư mục catalog khi --offline.

Usage:
    python script/build_lineage_from_design.py daily_dex_token_volume
    python script/build_lineage_from_design.py daily_dex_token_volume --offline
    python script/build_lineage_from_design.py --design-dir docs/foo/design
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'query'))
from metabase_query import exe_query

NON_TABLE_UPSTREAMS = {'node'}
SCHEMAS_TO_SKIP = {'default'}
DEV_SUFFIX = '_dev'
TABLE_REF_RE = re.compile(r'`([^`]+)`')

# Trạng thái bảng
STATUS_EXISTING = 'existing'
STATUS_NEW = 'new'
STATUS_DEV_ONLY = 'dev_only'

STATUS_LABEL = {
    STATUS_EXISTING: '✅ CÓ',
    STATUS_NEW: '❌ CẦN LÀM MỚI',
    STATUS_DEV_ONLY: '🔄 ĐANG DEV (bản _dev)',
}

MERMAID_CLASS = {
    STATUS_EXISTING: 'existing',
    STATUS_NEW: 'new',
    STATUS_DEV_ONLY: 'dev',
}


# ---------------------------------------------------------------- parse design

def read_lines(path):
    with open(path, encoding='utf-8') as f:
        return f.read().split('\n')


def parse_table_name(path, lines):
    """Lấy tên bảng từ heading đầu tiên (# schema.table), fallback: tên file."""
    for line in lines:
        if line.startswith('# '):
            name = line[2:].strip()
            if re.fullmatch(r'[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)+', name):
                return name
    return os.path.basename(path)[:-3]


def parse_header_input_tables(lines):
    """Lấy danh sách upstream từ row `list_input_tables` trong bảng Header (SQL Transform)."""
    in_header = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('### Header'):
            in_header = True
            continue
        if in_header:
            if stripped.startswith('## '):
                break
            if stripped.startswith('| list_input_tables'):
                # Dạng: | list_input_tables | `table1,table2,...` |
                parts = [p.strip() for p in stripped.split('|')]
                if len(parts) >= 3:
                    value = parts[2].strip('`').strip()
                    tables = [t.strip() for t in value.split(',') if t.strip()]
                    return tables
    return []


def parse_lineage_section(lines, label):
    """Trích xuất danh sách bảng từ bullet `- **<label> tables**: ...` trong mục ## Lineage."""
    in_lineage = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## '):
            if in_lineage:
                break
            if stripped == '## Lineage':
                in_lineage = True
            continue
        if in_lineage:
            pattern = f'- **{label} tables**:'
            if stripped.startswith(pattern):
                rest = stripped[len(pattern):]
                tables = TABLE_REF_RE.findall(rest)
                tables = [t for t in tables if t.strip() not in ('_None_', '_none_', 'None')]
                return tables
    return []


def parse_design_file(path):
    """Trích xuất thông tin lineage từ một file design markdown."""
    lines = read_lines(path)
    full_name = parse_table_name(path, lines)

    upstreams = parse_header_input_tables(lines)
    if not upstreams:
        upstreams = parse_lineage_section(lines, 'Upstream')
    upstreams = [u for u in upstreams if u not in NON_TABLE_UPSTREAMS]

    declared_downstreams = parse_lineage_section(lines, 'Downstream')

    return {
        'full_name': full_name,
        'upstreams': upstreams,
        'declared_downstreams': declared_downstreams,
    }


# ------------------------------------------------------------ existing tables

def get_warehouse_tables():
    """Truy vấn warehouse, trả về (bảng production, bảng _dev) dạng set full_name."""
    result = exe_query("SHOW SCHEMAS", engine='spark')
    schemas = [row[0] for row in result['rows'] if row[0] not in SCHEMAS_TO_SKIP]

    prod, dev = set(), set()
    for schema in schemas:
        r = exe_query(f"SHOW TABLES IN {schema}", engine='spark')
        for row in r['rows']:
            name = row[1] if len(row) > 1 else row[0]
            if name.endswith(DEV_SUFFIX):
                dev.add(f"{schema}.{name}")
            else:
                prod.add(f"{schema}.{name}")
    return prod, dev


def get_catalog_tables(catalog_dir):
    """Lấy danh sách bảng đã có từ thư mục catalog (dùng khi --offline)."""
    tables = set()
    if not os.path.isdir(catalog_dir):
        return tables
    for filename in os.listdir(catalog_dir):
        if filename.endswith('.md') and filename != 'lineage.md':
            tables.add(filename[:-3])
    return tables


def resolve_status(full_name, prod_tables, dev_tables):
    if full_name in prod_tables:
        return STATUS_EXISTING
    # Bảng production chưa có nhưng đã có bản <name>_dev đang test
    if f"{full_name}{DEV_SUFFIX}" in dev_tables:
        return STATUS_DEV_ONLY
    return STATUS_NEW


# ------------------------------------------------------------- build markdown

def build_lineage_md(problem, sorted_names, upstream_map, downstream_map,
                     status_map, declared_downstream_map, notes, source):
    node_id = {name: f"T{i}" for i, name in enumerate(sorted_names)}

    lines = [f"# Lineage — {problem}", ""]
    lines.append("Biểu đồ phụ thuộc (lineage) giữa các bảng trong thiết kế bài toán này, "
                 "được sinh tự động từ các file design trong thư mục này.")
    lines.append("Mũi tên `-->` nghĩa là \"được sử dụng để tạo ra\".")
    lines.append("")

    lines.append("## Chú thích trạng thái")
    lines.append("")
    lines.append(f"- **✅ CÓ**: bảng đã tồn tại trong warehouse (nguồn: {source})")
    lines.append("- **❌ CẦN LÀM MỚI**: bảng chưa tồn tại, cần build mới theo design")
    lines.append("- **🔄 ĐANG DEV**: chưa có bảng production nhưng đã có bảng `_dev` đang test")
    lines.append("")

    lines.append("## Mermaid Graph")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph LR")
    lines.append('    classDef existing fill:#d4edda,stroke:#28a745,color:#155724')
    lines.append('    classDef new fill:#fff3cd,stroke:#f0ad4e,color:#856404')
    lines.append('    classDef dev fill:#cce5ff,stroke:#007bff,color:#004085')
    for name in sorted_names:
        nid = node_id[name]
        cls = MERMAID_CLASS[status_map[name]]
        lines.append(f'    {nid}["{name}"]:::{cls}')
    for name in sorted_names:
        for up in upstream_map[name]:
            if up in node_id:
                lines.append(f"    {node_id[up]} --> {node_id[name]}")
    lines.append("```")
    lines.append("")

    lines.append("## Bảng chi tiết")
    lines.append("")
    lines.append("| Bảng | Trạng thái | Upstream | Downstream |")
    lines.append("|---|---|---|---|")
    for name in sorted_names:
        ups = upstream_map[name]
        downs = downstream_map[name]
        status = STATUS_LABEL[status_map[name]]
        up_str = ', '.join(ups) if ups else '_none_'
        down_str = ', '.join(downs) if downs else '_none_'
        lines.append(f"| `{name}` | {status} | {up_str} | {down_str} |")
    lines.append("")

    existing = [n for n in sorted_names if status_map[n] == STATUS_EXISTING]
    dev = [n for n in sorted_names if status_map[n] == STATUS_DEV_ONLY]
    new = [n for n in sorted_names if status_map[n] == STATUS_NEW]

    if existing:
        lines.append("## Bảng đã có")
        for n in existing:
            lines.append(f"- ✅ `{n}`")
        lines.append("")

    if dev:
        lines.append("## Bảng đang có bản _dev (chưa deploy production)")
        for n in dev:
            lines.append(f"- 🔄 `{n}`")
        lines.append("")

    if new:
        lines.append("## Bảng cần làm mới")
        for n in new:
            lines.append(f"- ❌ `{n}`")
        lines.append("")

    root_tables = [n for n in sorted_names if not upstream_map[n]]
    leaf_tables = [n for n in sorted_names if not downstream_map[n]]

    if root_tables:
        lines.append("## Root tables (không có upstream)")
        for t in root_tables:
            lines.append(f"- `{t}`")
        lines.append("")

    if leaf_tables:
        lines.append("## Leaf tables (không có downstream)")
        for t in leaf_tables:
            lines.append(f"- `{t}`")
        lines.append("")

    if notes:
        lines.append("## Ghi chú thiết kế cần kiểm tra")
        lines.extend(notes)
        lines.append("")

    return '\n'.join(lines)


# ------------------------------------------------------------------------ main

def main():
    parser = argparse.ArgumentParser(description="Xây dựng lineage.md từ các file design")
    parser.add_argument("problem", nargs="?", help="Tên bài toán (thư mục con của docs/), ví dụ daily_dex_token_volume")
    parser.add_argument("--design-dir", help="Đường dẫn trực tiếp tới thư mục design (thay thế problem)")
    parser.add_argument("--catalog-dir", default="catalog", help="Thư mục catalog dùng khi --offline (default: catalog)")
    parser.add_argument("--offline", action="store_true",
                        help="Không query warehouse, dùng thư mục catalog để xác định bảng đã có")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if args.design_dir:
        design_dir = os.path.join(project_root, args.design_dir)
    else:
        if not args.problem:
            parser.error("Cần cung cấp tên bài toán (positional) hoặc --design-dir")
        design_dir = os.path.join(project_root, 'docs', args.problem, 'design')

    if not os.path.isdir(design_dir):
        print(f"[ERROR] Không tìm thấy thư mục design: {design_dir}")
        sys.exit(1)

    catalog_dir = os.path.join(project_root, args.catalog_dir)

    # Bước 1: đọc các file design
    print(f"=== Đọc file design từ: {design_dir} ===")
    files = sorted(f for f in os.listdir(design_dir) if f.endswith('.md') and f != 'lineage.md')
    if not files:
        print("[ERROR] Không có file design nào trong thư mục design")
        sys.exit(1)

    designs = []
    upstream_map = {}
    declared_downstream_map = {}
    for filename in files:
        d = parse_design_file(os.path.join(design_dir, filename))
        designs.append(d)
        upstream_map[d['full_name']] = d['upstreams']
        declared_downstream_map[d['full_name']] = d['declared_downstreams']
        print(f"  - {d['full_name']}: {len(d['upstreams'])} upstream, "
              f"{len(d['declared_downstreams'])} downstream khai báo")
    print()

    # Bước 2: bổ sung các bảng tham chiếu (chỉ xuất hiện ở upstream, không có file design)
    referenced = set()
    for up_list in upstream_map.values():
        referenced.update(up_list)
    all_names = set(upstream_map.keys()) | referenced
    for name in all_names:
        if name not in upstream_map:
            upstream_map[name] = []
    print(f"Tổng số bảng trong graph: {len(all_names)} ({len(designs)} thiết kế, "
          f"{len(all_names) - len(designs)} tham chiếu ngoài)\n")

    # Bước 3: downstream = đảo ngược upstream (giống build_catalog.py)
    downstream_map = {name: [] for name in all_names}
    for name, ups in upstream_map.items():
        for up in ups:
            if up in downstream_map:
                downstream_map[up].append(name)

    # Bước 4: xác định trạng thái bảng (đã có / cần làm mới)
    print("=== Xác định trạng thái bảng ===")
    if args.offline:
        prod_tables = get_catalog_tables(catalog_dir)
        dev_tables = set()
        source = f"catalog ({catalog_dir})"
    else:
        try:
            prod_tables, dev_tables = get_warehouse_tables()
            source = "warehouse (Spark)"
        except Exception as e:
            print(f"  [WARN] Không query được warehouse ({e}) — dùng thư mục catalog làm nguồn.")
            prod_tables = get_catalog_tables(catalog_dir)
            dev_tables = set()
            source = f"catalog ({catalog_dir})"
    print(f"  Nguồn bảng đã có: {source}")

    status_map = {name: resolve_status(name, prod_tables, dev_tables) for name in all_names}
    for name in sorted(all_names):
        print(f"  - {STATUS_LABEL[status_map[name]]} {name}")
    print()

    # Bước 5: ghi chú — downstream khai báo nhưng không khớp graph suy từ upstream
    notes = []
    for name in sorted(declared_downstream_map):
        declared = declared_downstream_map[name]
        computed = downstream_map[name]
        for ds in declared:
            if ds not in computed:
                notes.append(
                    f"- ⚠️ `{name}` khai báo downstream `{ds}`, nhưng theo upstream trong file design "
                    f"của `{ds}` thì bảng này không đọc từ `{name}` — graph không có cạnh phụ thuộc giữa 2 bảng."
                )

    # Bước 6: sinh lineage.md
    sorted_names = sorted(all_names)
    content = build_lineage_md(
        args.problem or os.path.basename(os.path.dirname(design_dir)),
        sorted_names,
        upstream_map,
        downstream_map,
        status_map,
        declared_downstream_map,
        notes,
        source,
    )

    lineage_path = os.path.join(design_dir, 'lineage.md')
    with open(lineage_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"=== Hoàn tất! ===")
    print(f"Đã tạo: {lineage_path}")
    print(f"Số bảng đã có: {sum(1 for s in status_map.values() if s == STATUS_EXISTING)} | "
          f"đang dev: {sum(1 for s in status_map.values() if s == STATUS_DEV_ONLY)} | "
          f"cần làm mới: {sum(1 for s in status_map.values() if s == STATUS_NEW)}")


if __name__ == "__main__":
    main()
