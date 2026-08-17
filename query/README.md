# Query Scripts

Python scripts for interacting with the Data Warehouse via Metabase API.

## Installation

### 1. Install Libraries

```bash
pip install requests python-dotenv
```

### 2. Configure API Key

Create a `.env` file in the same directory with:

```
METABASE_API_KEY=<your API key>
```

To create an API key, visit: `http://localhost:53000/admin/settings/authentication`

---

## Scripts

### `get_example_table.py` — Fetch Sample Records from Table

Query 1 record from a table to view schema and sample data.

**Syntax:**
```bash
python get_example_table.py <table_name>
```

**Example:**
```bash
python get_example_table.py ethereum.transactions
```

**Returned Result:**
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

### `query_table.py` — Execute SQL Query

Execute a SELECT query on the Data Warehouse. The script will:
- **Block** queries that can modify data (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `REPLACE`, `MERGE`)
- **Require** queries to have a `LIMIT` clause

**Syntax:**
```bash
python query_table.py "<SQL_query>"
```

**Example:**
```bash
python query_table.py "SELECT * FROM ethereum.transactions LIMIT 10"
python query_table.py "SELECT hash, block_number FROM ethereum.transactions WHERE block_number > 1000000 LIMIT 50"
```

**Error when missing LIMIT:**
```
Error: Query must have a LIMIT clause to restrict the number of records returned.
Example: SELECT * FROM ethereum.transactions LIMIT 100
```

**Error when using destructive commands:**
```
Error: Query contains 'DROP' command that may modify data and is blocked.
Only SELECT queries (read-only) are allowed.
```

---

### `drop_table.py` — Drop Table

Drop a table from the Data Warehouse. Requires confirmation before execution to prevent accidental deletion.

**Syntax:**
```bash
python drop_table.py <table_name>
```

**Example:**
```bash
python drop_table.py ethereum.transactions
```

**Confirmation Process:**
```
Are you sure you want to drop table 'ethereum.transactions'? Enter table name to confirm: ethereum.transactions
Table 'ethereum.transactions' has been dropped successfully.
```

If the wrong table name is entered, the operation is cancelled:
```
Are you sure you want to drop table 'ethereum.transactions'? Enter table name to confirm: abc
Confirmation does not match. Drop operation cancelled.
```

---

### `check_table_properties.py` — Check Table Properties

Display tblproperties of a table on the Data Warehouse. Particularly useful for checking lock status and data range.

**Syntax:**
```bash
python check_table_properties.py <table_name>
```

**Example:**
```bash
python check_table_properties.py ethereum.blocks
```

**Returned Result:**
```
=== tblproperties of 'ethereum.blocks' ===

Property                        Value
--------------------------------------------------------------------------------
isLock                          0
frequenceType                   block
fromBlock                       12345678
toBlock                         12345999

=== Important Properties ===

  isLock (UNLOCKED): 0
  frequenceType: block
  fromBlock: 12345678
  toBlock: 12345999
```

**Important Properties:**
| Property | Description |
|---|---|
| `isLock` | Lock status: 1 = locked (job is writing), 0 = unlocked |
| `frequenceType` | Frequency type: `block`, `hour`, `minute`, `day` |
| `fromBlock`, `toBlock` | Current block range (if frequenceType=block) |
| `fromEpochSecond`, `toEpochSecond` | Current epoch second range (if frequenceType is minute/hour/day) |

---

### `unlock_table.py` — Unlock Table

Unlock a table when a job errors with "Table is Lock". Requires confirmation before execution.

**⚠️ Note:** Only use when you are certain no job is currently writing to the table.

**Syntax:**
```bash
python unlock_table.py <table_name>
```

**Example:**
```bash
python unlock_table.py ethereum.blocks
```

**Confirmation Process:**
```
⚠️  You are about to unlock table 'ethereum.blocks'.
    Command to execute: ALTER TABLE ethereum.blocks SET TBLPROPERTIES (isLock=0)

Enter table name to confirm: ethereum.blocks
✅ Table 'ethereum.blocks' has been unlocked successfully.
```

### `insert_dev_data.py` — Insert Data into `_dev` Table

Insert data into tables with `_dev` suffix for testing purposes (add edge case data, prepare test data, etc.). The script **ONLY allows** inserting into `_dev` tables — production tables are blocked. If the INSERT uses `SELECT`, it **must have `LIMIT`**.

**Syntax:**
```bash
python insert_dev_data.py "<INSERT_SQL>"
python insert_dev_data.py -f insert.sql
```

**Example:**
```bash
# Insert using VALUES
python insert_dev_data.py "INSERT INTO ethereum.transactions_dev (hash, block_number) VALUES ('0xabc', 123)"

# Insert from SELECT (must have LIMIT)
python insert_dev_data.py "INSERT INTO ethereum.transactions_dev SELECT * FROM ethereum.transactions_dev LIMIT 10"

# Insert Overwrite (must have LIMIT if using SELECT)
python insert_dev_data.py "INSERT OVERWRITE ethereum.transactions_dev SELECT * FROM ethereum.transactions_dev LIMIT 10"
```

**Error when inserting into production table (no `_dev`):**
```
Error: Target table 'ethereum.transactions' does not have _dev suffix. Only inserts into _dev tables are allowed to protect production.
```

**Error when INSERT SELECT is missing LIMIT:**
```
Error: INSERT SELECT statement must have a LIMIT clause to restrict the number of records.
```

---

### `set_table_property.py` — Set Properties on `_dev` Table

Set TBLPROPERTIES on tables with `_dev` suffix for testing purposes (adjust `fromBlock`, `toBlock`, `isLock`, `frequenceType`, etc.). The script **ONLY allows** setting on `_dev` tables — production tables are blocked.

**Syntax:**
```bash
python set_table_property.py "<ALTER_SQL>"
python set_table_property.py -f set_props.sql
```

**Example:**
```bash
# Set fromBlock
python set_table_property.py "ALTER TABLE ethereum.transactions_dev SET TBLPROPERTIES (fromBlock=1000)"

# Set multiple properties
python set_table_property.py "ALTER TABLE ethereum.transactions_dev SET TBLPROPERTIES (fromBlock=1000, toBlock=2000)"
```

**Error when setting on production table (no `_dev`):**
```
Error: Target table 'ethereum.transactions' does not have _dev suffix. Only setting properties on _dev tables is allowed to protect production.
```

---

## Project Structure

```
query/
├── .env                      # Environment variables (API key) — not committed to git
├── env_example               # Example .env configuration file
├── metabase_query.py         # Core module for calling Metabase API
├── get_example_table.py      # Fetch sample records from table
├── query_table.py            # Execute SQL queries (read-only)
├── drop_table.py             # Drop table (with confirmation)
├── check_table_properties.py # Check table tblproperties
├── unlock_table.py           # Unlock table (set isLock=0)
├── insert_dev_data.py        # Insert data into _dev table (_dev only)
└── set_table_property.py     # Set TBLPROPERTIES on _dev table (_dev only)
```