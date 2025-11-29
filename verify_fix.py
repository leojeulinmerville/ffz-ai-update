import requests
import json
import sys

def test_registration_and_login():
    base_url = "http://localhost:8000"
    email = "test_login_fix@example.com"
    password = "Password123!"
    
    # 1. Register
    print(f"Attempting to register {email}...")
    register_url = f"{base_url}/api/public/register"
    payload = {
        "email": email,
        "password": password,
        "first_name": "Leo",
        "last_name": "Jeulin",
        "language": "fr",
        "favorite_team": "Bologna",
        "leagues": ["Serie A", "Premier League"]
    }
    
    try:
        resp = requests.post(register_url, json=payload)
        print(f"Register Status: {resp.status_code}")
        print(f"Register Body: {resp.text}")
        
        if resp.status_code not in [200, 201]:
            print(f"Registration failed with status {resp.status_code}. It might already exist. Proceeding to login...")
        else:
            print("Registration successful.")

        # 2. Login
        print(f"Attempting to login...")
        login_url = f"{base_url}/auth/login"
        login_payload = {"email": email, "password": password}
        
        login_resp = requests.post(login_url, json=login_payload)
        print(f"Login Status: {login_resp.status_code}")
        print(f"Login Body: {login_resp.text}")
        
        if login_resp.status_code == 200:
            print("Login successful!")
            token = login_resp.json().get("access_token")
            print(f"Token received: {token[:10]}...")
        else:
            print("Login failed.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_registration_and_login()
