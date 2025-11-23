import requests, json
url = 'http://localhost:8000/auth/login'
payload = {'email': 'test@ffz.com', 'password': 'password123'}
resp = requests.post(url, json=payload)
print('Status:', resp.status_code)
print('Body:', resp.text)
