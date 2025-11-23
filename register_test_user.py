import requests
import json

url = "http://localhost:8000/api/public/register"
payload = {
    "email": "test@ffz.com",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "favorite_team": "Bologna",
    "language": "en"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✓ User created successfully!")
        print("  Email: test@ffz.com")
        print("  Password: password123")
        print("\nNow manually set is_verified=1 in database...")
        
        import sqlite3
        conn = sqlite3.connect('ffz.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_verified = 1 WHERE email = 'test@ffz.com'")
        conn.commit()
        print("✓ User verified!")
        conn.close()
except Exception as e:
    print(f"Error: {e}")
