import psycopg2
import sys

creds = [
    ("ffz_user", "ffz_password"),
    ("postgres", "posgres"), # User provided
    ("postgres", "postgres"), # Standard default
    ("postgres", "password"), # Common default
]

for user, password in creds:
    url = f"postgresql://{user}:{password}@localhost:5432/ffz_db"
    print(f"Testing {user}:{password}...")
    try:
        conn = psycopg2.connect(url)
        print(f"SUCCESS with {user}:{password}")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"FAILED with {user}:{password}: {e}")
        # Try connecting to default 'postgres' db in case 'ffz_db' doesn't exist
        try:
            url_default = f"postgresql://{user}:{password}@localhost:5432/postgres"
            conn = psycopg2.connect(url_default)
            print(f"SUCCESS with {user}:{password} (connected to 'postgres' db, 'ffz_db' might be missing)")
            conn.close()
            sys.exit(0)
        except Exception as e2:
             print(f"FAILED with {user}:{password} (postgres db): {e2}")

print("All attempts failed.")
sys.exit(1)
