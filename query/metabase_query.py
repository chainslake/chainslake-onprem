import os
import requests
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Database IDs in Metabase (change if re-setup from scratch)
DATABASES = {
    'spark': 2,
    'trino': 3,
}

METABASE_URL = os.getenv('METABASE_URL', 'http://localhost:53000')


def _extract_error(resp):
    """Extract clear error message from Metabase response."""
    try:
        body = resp.json()
    except Exception:
        return resp.text

    # Errors from Spark/Trino via Metabase
    via = body.get('via', [])
    for item in via:
        error_msg = item.get('error', '')
        if error_msg:
            # Truncate Java stack trace, keep only the first line with the error message
            first_line = error_msg.split('\n')[0].strip()
            # Remove prefix if present (e.g.: "Error executing query: org.apache.hive...")
            if ': ' in first_line:
                parts = first_line.split(': ', 2)
                if len(parts) >= 3:
                    first_line = parts[2]
                elif len(parts) == 2:
                    first_line = parts[1]
            return first_line

    # Errors from Metabase directly
    errors = body.get('errors', [])
    if errors:
        return '; '.join(errors)

    message = body.get('message', '')
    if message:
        return message

    return resp.text


def exe_query(sql, engine='spark'):
    """
    Execute SQL via Metabase API.

    Args:
        sql: SQL query statement
        engine: 'spark' or 'trino'

    Returns:
        dict with 'rows' and 'cols'
    """
    database_id = DATABASES.get(engine)
    if database_id is None:
        raise ValueError(f"Unknown engine '{engine}'. Available: {list(DATABASES.keys())}")

    api_key = os.getenv('METABASE_API_KEY')
    if not api_key:
        raise RuntimeError("METABASE_API_KEY not set in query/.env")

    body = {
        "database": database_id,
        "type": "native",
        "native": {
            "query": sql
        }
    }
    header = {
        'X-API-KEY': api_key
    }
    resp = requests.post(f"{METABASE_URL}/api/dataset", json=body, headers=header, timeout=60)

    if not resp.ok:
        error_detail = _extract_error(resp)
        raise RuntimeError(f"Query failed (HTTP {resp.status_code}):\n{error_detail}")

    data = resp.json()['data']
    return {
        'rows': data['rows'],
        'cols': [{'name': col['name'], 'type': col['base_type']} for col in data['cols']]
    }
