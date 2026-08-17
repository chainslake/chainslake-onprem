#!/usr/bin/env python3
"""
Build lineage.md from Data Architect design files.

Reads all markdown files in a problem's design directory
(docs/<problem>/design/*.md), extracts upstream/downstream relationships between
tables, determines table status (exists in warehouse / needs to be built), and
generates lineage.md (Mermaid graph + detail table) in the same design directory —
similar format to the lineage.md in the catalog directory created by build_catalog.py.

Upstream sources are taken from the `list_input_tables` row in the Header table (SQL Transform section)
of each design file; downstream is inferred by reversing upstream
(same as build_catalog.py). Table status is determined by querying
the warehouse (Spark), or using the catalog directory when --offline.

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

# Table status
STATUS_EXISTING = 'existing'
STATUS_NEW = 'new'
STATUS_DEV_ONLY = 'dev_only'

STATUS_LABEL = {
    STATUS_EXISTING: '✅ EXISTS',
    STATUS_NEW: '❌ NEEDS BUILDING',
    STATUS_DEV_ONLY: '🔄 IN DEV (_dev version)',
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
    """Get table name from first heading (# schema.table), fallback: filename."""
    for line in lines:
        if line.startswith('# '):
            name = line[2:].strip()
            if re.fullmatch(r'[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)+', name):
                return name
    return os.path.basename(path)[:-3]


def parse_header_input_tables(lines):
    """Get upstream list from `list_input_tables` row in Header table (SQL Transform)."""
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
                # Format: | list_input_tables | `table1,table2,...` |
                parts = [p.strip() for p in stripped.split('|')]
                if len(parts) >= 3:
                    value = parts[2].strip('`').strip()
                    tables = [t.strip() for t in value.split(',') if t.strip()]
                    return tables
    return []


def parse_lineage_section(lines, label):
    """Extract table list from bullet `- **<label> tables**: ...` in ## Lineage section."""
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
    """Extract lineage info from a design markdown file."""
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
    """Query warehouse, return (production tables, _dev tables) as full_name sets."""
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
    """Get existing tables list from catalog directory (used with --offline)."""
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
    # Production table not yet available but _dev version exists and is being tested
    if f"{full_name}{DEV_SUFFIX}" in dev_tables:
        return STATUS_DEV_ONLY
    return STATUS_NEW


# ------------------------------------------------------------- build markdown

def build_lineage_md(problem, sorted_names, upstream_map, downstream_map,
                     status_map, declared_downstream_map, notes, source):
    node_id = {name: f"T{i}" for i, name in enumerate(sorted_names)}

    lines = [f"# Lineage — {problem}", ""]
    lines.append("Dependency diagram (lineage) between tables in this problem design, "
                 "auto-generated from design files in this directory.")
    lines.append("Arrow `-->` means \"is used to create\".")
    lines.append("")

    lines.append("## Status Legend")
    lines.append("")
    lines.append(f"- **✅ EXISTS**: table already exists in warehouse (source: {source})")
    lines.append("- **❌ NEEDS BUILDING**: table does not exist yet, needs to be built per design")
    lines.append("- **🔄 IN DEV**: no production table yet, but `_dev` version is being tested")
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

    lines.append("## Detail Table")
    lines.append("")
    lines.append("| Table | Status | Upstream | Downstream |")
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
        lines.append("## Existing Tables")
        for n in existing:
            lines.append(f"- ✅ `{n}`")
        lines.append("")

    if dev:
        lines.append("## Tables with _dev Version (not yet deployed to production)")
        for n in dev:
            lines.append(f"- 🔄 `{n}`")
        lines.append("")

    if new:
        lines.append("## Tables That Need Building")
        for n in new:
            lines.append(f"- ❌ `{n}`")
        lines.append("")

    root_tables = [n for n in sorted_names if not upstream_map[n]]
    leaf_tables = [n for n in sorted_names if not downstream_map[n]]

    if root_tables:
        lines.append("## Root tables (no upstream)")
        for t in root_tables:
            lines.append(f"- `{t}`")
        lines.append("")

    if leaf_tables:
        lines.append("## Leaf tables (no downstream)")
        for t in leaf_tables:
            lines.append(f"- `{t}`")
        lines.append("")

    if notes:
        lines.append("## Design Notes Requiring Review")
        lines.extend(notes)
        lines.append("")

    return '\n'.join(lines)


# ------------------------------------------------------------------------ main

def main():
    parser = argparse.ArgumentParser(description="Build lineage.md from design files")
    parser.add_argument("problem", nargs="?", help="Problem name (subdirectory of docs/), e.g. daily_dex_token_volume")
    parser.add_argument("--design-dir", help="Direct path to design directory (overrides problem)")
    parser.add_argument("--catalog-dir", default="catalog", help="Catalog directory used with --offline (default: catalog)")
    parser.add_argument("--offline", action="store_true",
                        help="Don't query warehouse, use catalog directory to determine existing tables")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if args.design_dir:
        design_dir = os.path.join(project_root, args.design_dir)
    else:
        if not args.problem:
            parser.error("Must provide problem name (positional) or --design-dir")
        design_dir = os.path.join(project_root, 'docs', args.problem, 'design')

    if not os.path.isdir(design_dir):
        print(f"[ERROR] Design directory not found: {design_dir}")
        sys.exit(1)

    catalog_dir = os.path.join(project_root, args.catalog_dir)

    # Step 1: read design files
    print(f"=== Reading design files from: {design_dir} ===")
    files = sorted(f for f in os.listdir(design_dir) if f.endswith('.md') and f != 'lineage.md')
    if not files:
        print("[ERROR] No design files in the design directory")
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
              f"{len(d['declared_downstreams'])} declared downstream")
    print()

    # Step 2: add referenced tables (only appear in upstream, no design file)
    referenced = set()
    for up_list in upstream_map.values():
        referenced.update(up_list)
    all_names = set(upstream_map.keys()) | referenced
    for name in all_names:
        if name not in upstream_map:
            upstream_map[name] = []
    print(f"Total tables in graph: {len(all_names)} ({len(designs)} designs, "
          f"{len(all_names) - len(designs)} external references)\n")

    # Step 3: downstream = reverse of upstream (same as build_catalog.py)
    downstream_map = {name: [] for name in all_names}
    for name, ups in upstream_map.items():
        for up in ups:
            if up in downstream_map:
                downstream_map[up].append(name)

    # Step 4: determine table status (exists / needs building)
    print("=== Determining table status ===")
    if args.offline:
        prod_tables = get_catalog_tables(catalog_dir)
        dev_tables = set()
        source = f"catalog ({catalog_dir})"
    else:
        try:
            prod_tables, dev_tables = get_warehouse_tables()
            source = "warehouse (Spark)"
        except Exception as e:
            print(f"  [WARN] Cannot query warehouse ({e}) — using catalog directory as source.")
            prod_tables = get_catalog_tables(catalog_dir)
            dev_tables = set()
            source = f"catalog ({catalog_dir})"
    print(f"  Table source: {source}")

    status_map = {name: resolve_status(name, prod_tables, dev_tables) for name in all_names}
    for name in sorted(all_names):
        print(f"  - {STATUS_LABEL[status_map[name]]} {name}")
    print()

    # Step 5: notes — declared downstream doesn't match upstream-inferred graph
    notes = []
    for name in sorted(declared_downstream_map):
        declared = declared_downstream_map[name]
        computed = downstream_map[name]
        for ds in declared:
            if ds not in computed:
                notes.append(
                    f"- Warning: `{name}` declares downstream `{ds}`, but according to upstream in the design file "
                    f"of `{ds}`, this table does not read from `{name}` — no dependency edge between the two tables."
                )

    # Step 6: generate lineage.md
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
    print(f"=== Done! ===")
    print(f"Generated: {lineage_path}")
    print(f"Existing: {sum(1 for s in status_map.values() if s == STATUS_EXISTING)} | "
          f"In dev: {sum(1 for s in status_map.values() if s == STATUS_DEV_ONLY)} | "
          f"Needs building: {sum(1 for s in status_map.values() if s == STATUS_NEW)}")


if __name__ == "__main__":
    main()
