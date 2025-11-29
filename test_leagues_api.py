import requests
import json

# Test the /meta/leagues endpoint
url = "http://localhost:8000/meta/leagues"
response = requests.get(url)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {response.headers.get('content-type')}")
print(f"\nResponse Body:")
print(json.dumps(response.json(), indent=2))
