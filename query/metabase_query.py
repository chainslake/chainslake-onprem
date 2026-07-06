import requests
import json
import os
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

def exe_query(sql):
    url = 'http://localhost:53000/api/dataset'
    api_key = os.getenv('METABASE_API_KEY')
    body = {
        "lib/type": "mbql/query",
        "database": 2,
        "stages": [
            {
                "native": sql,
                "lib/type": "mbql.stage/native",
                "template-tags": {}
            }
        ],
        "parameters": []
    }
    header = {
        'X-API-KEY': api_key
    }
    data = requests.post(url, json=body, headers=header).json()['data']
    return {
        'rows': data['rows'],
        'cols': [{'name': col['name'], 'type': col['base_type']} for col in data['cols']]
    }