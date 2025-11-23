import requests
import json

url = "http://localhost:8000/api/public/register"
payload = {
    "email": "test_vision@example.com",
    "password": "password123",
    "first_name": "Vision",
    "last_name": "Tester",
    "favorite_team": "Bologna"
}
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
