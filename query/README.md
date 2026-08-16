# Query Scripts

A set of Python scripts to interact with the Data Warehouse through the Metabase API.

## Setup

### 1. Install dependencies

```bash
pip install requests python-dotenv
```

### 2. Configure the API Key

Create a `.env` file in the same directory with the following content:

```
METABASE_API_KEY=<Your API key>
```

To create an API key, visit: `http://localhost:53000/admin/settings/authentication`

---

## Scripts

### `get_example_table.py` — Get sample records from a table

Query 1 record from the table to view its schema and sample data.

**Usage:**
```bash
python get_example_table.py <table_name>
```

**Example:**
```bash
python get_example_table.py ethereum.transactions
```

**Output:**
```json
{
  "rows": [["0xabc...", 1234567, ...]],
  "cols": [
    {"name": "hash", "type": "type/Text"},
    {"name": "block_number", "type": "type/BigInteger"}
  ]
}
```

---

### `query_table.py` — Execute an SQL query

Execute a SELECT query on the Data Warehouse. The script will:
- **Block** queries that can modify data (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `REPLACE`, `MERGE`)
- **Require** the query to include a `LIMIT` clause

**Usage:**
```bash
python query_table.py "<sql_query>"
```

**Examples:**
```bash
python query_table.py "SELECT * FROM ethereum.transactions LIMIT 10"
python query_table.py "SELECT hash, block_number FROM ethereum.transactions WHERE block_number > 1000000 LIMIT 50"
```

**Error when LIMIT is missing:**
```
Error: The query must include a LIMIT clause to limit the number of returned records.
Example: SELECT * FROM ethereum.transactions LIMIT 100
```

**Error when using a destructive command:**
```
Error: The query contains the 'DROP' command, which can modify data and is blocked.
Only SELECT (read-only) queries are allowed.
```

---

### `drop_table.py` — Drop a table

Drop a table from the Data Warehouse. The script requires confirmation before proceeding to prevent accidental drops.

**Usage:**
```bash
python drop_table.py <table_name>
```

**Example:**
```bash
python drop_table.py ethereum.transactions
```

**Confirmation flow:**
```
Are you sure you want to drop table 'ethereum.transactions'? Type the table name to confirm: ethereum.transactions
Table 'ethereum.transactions' dropped successfully.
```

If an incorrect table name is entered, the operation is cancelled:
```
Are you sure you want to drop table 'ethereum.transactions'? Type the table name to confirm: abc
Confirmation does not match. Table drop operation cancelled.
```

---

### `check_table_properties.py` — Check table properties

Display the tblproperties of a table in the Data Warehouse. Particularly useful for checking the lock status and data range.

**Usage:**
```bash
python check_table_properties.py <table_name>
```

**Example:**
```bash
python check_table_properties.py ethereum.blocks
```

**Output:**
```
=== tblproperties of 'ethereum.blocks' ===

Property                        Value
--------------------------------------------------------------------------------
isLock                          0
frequenceType                   block
fromBlock                       12345678
toBlock                         12345999

=== Important properties ===

  isLock (UNLOCKED): 0
  frequenceType: block
  fromBlock: 12345678
  toBlock: 12345999
```

**Important properties:**
| Property | Description |
|---|---|
| `isLock` | Lock status: 1 = locked (a job is writing), 0 = unlocked |
| `frequenceType` | Frequency type: `block`, `hour`, `minute`, `day` |
| `fromBlock`, `toBlock` | Existing block range (if frequenceType=block) |
| `fromEpochSecond`, `toEpochSecond` | Existing epoch second range (if frequenceType is minute/hour/day) |

---

### `unlock_table.py` — Unlock a table

Unlock a table when a job fails with the "Table is Lock" error. Requires confirmation before proceeding.

**⚠️ Note:** Only use when you are certain no job is currently writing data to the table.

**Usage:**
```bash
python unlock_table.py <table_name>
```

**Example:**
```bash
python unlock_table.py ethereum.blocks
```

**Confirmation flow:**
```
⚠️  You are about to unlock table 'ethereum.blocks'.
    Command to be executed: ALTER TABLE ethereum.blocks SET TBLPROPERTIES (isLock=0)

Type the table name to confirm: ethereum.blocks
✅ Table 'ethereum.blocks' unlocked successfully.
```

---

## Project structure

```
query/
├── .env                      # Environment variables (API key) — not committed to git
├── env_example               # Sample .env configuration file
├── metabase_query.py         # Core module for calling the Metabase API
├── get_example_table.py      # Get sample records from a table
├── query_table.py            # Execute an SQL query (read-only)
├── drop_table.py             # Drop a table (with confirmation)
├── check_table_properties.py # Check the tblproperties of a table
└── unlock_table.py           # Unlock a table (set isLock=0)
```
