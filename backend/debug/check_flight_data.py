import requests
import json

# API URL
url = "http://127.0.0.1:5000/api/flight/search"

# 查詢參數
params = {
    "departure": "TPE",
    "arrival": "DPS",
    "date": "2025-04-07"
}

# 發送請求
response = requests.get(url, params=params)
print(f"Status code: {response.status_code}")

# 如果成功，打印響應
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(f"Error: {response.text}")