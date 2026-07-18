import os
import requests
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Database IDs trong Metabase (thay đổi nếu setup lại từ đầu)
DATABASES = {
    'spark': 2,
    'trino': 3,
}

METABASE_URL = os.getenv('METABASE_URL', 'http://localhost:53000')


def exe_query(sql, engine='spark'):
    """
    Thực thi SQL qua Metabase API.

    Args:
        sql: Câu truy vấn SQL
        engine: 'spark' hoặc 'trino'

    Returns:
        dict với 'rows' và 'cols'
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
    resp.raise_for_status()
    data = resp.json()['data']
    return {
        'rows': data['rows'],
        'cols': [{'name': col['name'], 'type': col['base_type']} for col in data['cols']]
    }
