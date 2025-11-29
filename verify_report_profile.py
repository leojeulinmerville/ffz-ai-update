import requests, json, sys
BASE_URL = 'http://localhost:8000'
EMAIL = 'test_login_fix@example.com'
PASSWORD = 'Password123!'

def login():
    resp = requests.post(f'{BASE_URL}/auth/login', json={'email': EMAIL, 'password': PASSWORD})
    if resp.status_code != 200:
        print('Login failed', resp.status_code, resp.text)
        sys.exit(1)
    token = resp.json().get('access_token')
    print('Login token:', token)
    return token

def get_profile(token):
    resp = requests.get(f'{BASE_URL}/api/user/profile', headers={'Authorization': f'Bearer {token}'})
    print('GET profile status:', resp.status_code)
    print('Profile data:', resp.json())
    return resp.json()

def update_profile(token, data):
    resp = requests.put(f'{BASE_URL}/api/user/profile', json=data, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    print('PUT update profile status:', resp.status_code)
    print('Updated profile:', resp.json())

def generate_report(token):
    resp = requests.post(f'{BASE_URL}/news/generate', headers={'Authorization': f'Bearer {token}'})
    print('POST generate report status:', resp.status_code)
    if resp.ok:
        print('Report response:', resp.json())
    else:
        print('Report error:', resp.text)

if __name__ == '__main__':
    token = login()
    get_profile(token)
    update_profile(token, {'language': 'es', 'favorite_team': 'Juventus'})
    get_profile(token)
    generate_report(token)
