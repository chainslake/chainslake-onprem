---
name: setup-metabase
description: Set up Metabase on on-premise environment — create admin account, connect databases, create API key, authenticate CLI
---

# Skill: Setup Metabase On-Premise

## Description
Set up Metabase on an on-premise environment: create admin account, connect databases (SparkSQL/Trino), create API key for automation, and use Metabase CLI (`mb`) for management.

## When to Use
- Metabase container is started (port 53000)
- First access to `http://localhost:53000` — no admin account exists yet
- Need to reset Metabase from scratch (reset database)
- Metabase v0.62+ (supports Metabase CLI `mb`)

## Install Metabase CLI

```bash
# Install (requires Node.js v18+)
npm install -g @metabase/cli

# Verify
mb --version

# Login
mb auth login --url http://localhost:53000 --api-key <API_KEY>

# Check status
mb auth status
```

## Implementation Steps

### Step 1: Configure Credentials in `script/.env`

The script reads all credentials from `script/.env`. **Do NOT pass passwords via command line.**

```bash
# If script/.env doesn't exist, copy from template
cp script/env_example script/.env
```

Edit `script/.env` with actual values:

```env
METABASE_URL=http://localhost:53000
METABASE_EMAIL=admin@chainslake.com
METABASE_PASSWORD=<your_password_here>
METABASE_SITE_NAME=Chainslake Warehouse
```

### Step 2: Run Setup Script

```bash
python script/setup_metabase.py
```

Script automatically:
1. Waits for Metabase to be ready (checks `/api/health`)
2. Creates admin account via `/api/setup` API
3. Creates API key and writes to `query/.env`
4. Adds SparkSQL database connection
5. Adds Trino database connection (if Starburst driver available)
6. Authenticates Metabase CLI (`mb auth login`)

**Optional parameters:**
```bash
python script/setup_metabase.py --skip-databases    # Skip adding databases
python script/setup_metabase.py --skip-cli          # Bypass CLI auth
python script/setup_metabase.py --api-key-file path/to/.env  # Change API key output location
```

### Step 2: Use Metabase CLI for Management

```bash
# List databases
mb db list

# View database details
mb db get <db-id>

# Sync schema
mb db sync-schema <db-id>

# Rescan field values
mb db rescan-values <db-id>

# List schemas
mb db schemas <db-id>

# List tables in schema
mb db schema-tables <db-id> <schema-name>

# List cards (questions/models/metrics)
mb card list

# List dashboards
mb dashboard list

# List collections
mb collection list

# Search content
mb search <query>

# View settings
mb setting get <key>
```

### Step 3: Verify Results

1. Access `http://localhost:53000` — login with admin credentials
2. Go to **Settings → Admin → Databases** — verify Spark/Trino have been added
3. File `query/.env` has `METABASE_API_KEY=...`

## Notes / Gotchas

### API `/api/setup` — Metabase v0.62.x Format
Metabase v0.62.x OSS **does NOT support** `MB_CONFIG_FILE` (Pro/Enterprise only).
The `/api/setup` endpoint requires a special format:

```json
{
  "token": "<setup-token from /api/session/properties>",
  "user": {"email": "...", "first_name": "...", "last_name": "...", "password": "..."},
  "prefs": {"site_name": "...", "site_locale": "en"},
  "database": null
}
```

**Common mistakes:**
- Sending `email` at root level → error `"email": ["should be a string, received: nil"]`
- Using `invited_email` at root level → same error
- Password too weak (e.g., `admin123456`) → error `"password is too common"`
- Sending `password` at root level instead of inside `user` object → nil error

### Trino Connection
Starburst Metabase driver requires SSL. If local Trino server doesn't have SSL enabled:
- Error `"TLS/SSL is required for authentication with username and password"`
- Set `ssl: true, insecure: true` in details
- If still failing (SSL message error), skip Trino — SparkSQL is sufficient

### API Key
- Endpoint: `POST /api/api-key` (requires session token)
- Key is returned only once via `unmasked_key`
- Write it immediately to `query/.env`

### Metabase CLI (`mb`)
- Requires Metabase v0.58+ (currently v0.62.4.3)
- `mb auth login` supports API key or browser OAuth (v0.62+)
- CLI does not support `db create` — use API `/api/database` to add databases
- CLI supports: list/get/sync/rescan for databases; CRUD for cards, dashboards, collections
- Default output is text, add `--json` for JSON
- Use `mb skills get core` to view detailed conventions

## Real-world Example
- Date: 2026-07-12
- Metabase v0.62.4.3 OSS
- Metabase CLI v0.2.1
- Setup succeeded with user nested object format
- SparkSQL: OK, Trino: OK
- CLI authenticated and working normally