import requests
import json
import os
import argparse
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

def get_example_table(table):
    return exe_query(f"select * from {table} limit 1")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lấy 1 bản ghi mẫu từ bảng trong datawarehouse qua Metabase")
    parser.add_argument("table", help="Tên bảng, ví dụ: ethereum.transactions")
    args = parser.parse_args()

    result = get_example_table(args.table)
    print(result)