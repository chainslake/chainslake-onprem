# Skill: Setup Metabase On-Premise

## Description
Setting up Metabase in an on-premise environment: creating the admin account, connecting databases (SparkSQL/Trino), creating an API key for automation, and using the Metabase CLI (`mb`) for management.

## Applicability Conditions
- The Metabase container has been started (port 53000)
- First-time access to `http://localhost:53000` — no admin account yet
- Need to redo the Metabase setup from scratch (database reset)
- Metabase v0.62+ (supports the Metabase CLI `mb`)

## Install the Metabase CLI

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

## Steps

### Step 1: Configure credentials in `script/.env`

The script reads all credentials from `script/.env`. **DO NOT pass passwords via the command line.**

```bash
# If script/.env does not exist, copy from the template
cp script/env_example script/.env
```

Edit `script/.env` with the actual information:

```env
METABASE_URL=http://localhost:53000
METABASE_EMAIL=admin@chainslake.com
METABASE_PASSWORD=<your_password_here>
METABASE_SITE_NAME=Chainslake Warehouse
```

### Step 2: Run the setup script

```bash
python script/setup_metabase.py
```

The script automatically:
1. Waits for Metabase to be ready (checks `/api/health`)
2. Creates the admin account via the `/api/setup` API
3. Creates the API key and writes it to `query/.env`
4. Adds the SparkSQL database connection
5. Adds the Trino database connection (if the Starburst driver is available)
6. Authenticates the Metabase CLI (`mb auth login`)

**Optional parameters:**
```bash
python script/setup_metabase.py --skip-databases    # Skip adding databases
python script/setup_metabase.py --skip-cli          # Bypass CLI auth
python script/setup_metabase.py --api-key-file path/to/.env  # Change where the API key is written
```

### Step 2: Use the Metabase CLI to manage

```bash
# List databases
mb db list

# View database details
mb db get <db-id>

# Sync the schema
mb db sync-schema <db-id>

# Rescan field values
mb db rescan-values <db-id>

# List schemas
mb db schemas <db-id>

# List tables in a schema
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

### Step 3: Verify the results

1. Access `http://localhost:53000` — log in with the admin credentials
2. Go to **Settings → Admin → Databases** — verify Spark/Trino have been added
3. The file `query/.env` now contains `METABASE_API_KEY=...`

## Notes / Gotchas

### API `/api/setup` — Metabase v0.62.x format
Metabase v0.62.x OSS **does not support** `MB_CONFIG_FILE` (Pro/Enterprise only).
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
- Sending `email` at the root level → error `"email": ["should be a string, received: nil"]`
- Using `invited_email` at the root level → the same error as above
- Password too weak (e.g., `admin123456`) → error `"password is too common"`
- Sending `password` at the root level instead of inside the `user` object → nil error

### Trino connection
The Starburst Metabase driver requires SSL. If the local Trino server does not have SSL enabled:
- Error `"TLS/SSL is required for authentication with username and password"`
- Set `ssl: true, insecure: true` in the details
- If it still fails (SSL message error), skip Trino — SparkSQL is sufficient

### API Key
- Endpoint: `POST /api/api-key` (requires a session token)
- The key is returned only once via `unmasked_key`
- Write it to `query/.env` immediately

### Metabase CLI (`mb`)
- Requires Metabase v0.58+ (currently v0.62.4.3)
- `mb auth login` supports API key or browser OAuth (v0.62+)
- The CLI does not support `db create` — use the `/api/database` API to add databases
- The CLI supports: list/get/sync/rescan for databases; CRUD for cards, dashboards, collections
- Output is text by default, add `--json` to get JSON
- Use `mb skills get core` to see detailed conventions

## Real-World Example
- Date: 2026-07-12
- Metabase v0.62.4.3 OSS
- Metabase CLI v0.2.1
- Setup succeeded with the nested user object format
- SparkSQL: OK, Trino: OK
- CLI authenticated and working normally
