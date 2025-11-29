import psycopg2
import os

# Hardcoded for simplicity and to avoid import issues
DATABASE_URL = "postgresql://ffz_user:ffz_password@localhost:5432/ffz_db?client_encoding=utf8"

def verify():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        print(f"Result: {result}")
        conn.close()
        print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {repr(e)}")

if __name__ == "__main__":
    verify()
