import requests
import json

url = "http://localhost:8000/api/public/register"
payload = {
    "email": "leojeulinmerville@icloud.com",
    "password": "Libourne33!",
    "first_name": "Leo",
    "last_name": "Jeulin",
    "favorite_team": "Bologna",
    "language": "fr"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✓ Registration successful!")
        # Now verify the user
        import sqlite3
        conn = sqlite3.connect('ffz.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_verified = 1 WHERE email = ?", (payload['email'],))
        conn.commit()
        print("✓ User verified!")
        conn.close()
    else:
        print(f"\n✗ Registration failed")
        print(f"Error details: {response.json() if response.headers.get('content-type') == 'application/json' else response.text}")
except Exception as e:
    print(f"Error: {e}")
