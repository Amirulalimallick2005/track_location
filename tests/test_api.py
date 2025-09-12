# tests/test_api.py
import requests

BASE = "http://localhost:5000"
url = BASE + "/api/check_safety"
payload = {"latitude": 26.78, "longitude": 91.70}

r = requests.post(url, json=payload, timeout=5)
print("Status:", r.status_code)
print("Response:", r.json())
