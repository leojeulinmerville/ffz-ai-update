import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to 'postgres' db to create new db
conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/postgres")
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

db_name = "ffz_db"

try:
    cur.execute(f"CREATE DATABASE {db_name};")
    print(f"Database {db_name} created successfully.")
except psycopg2.errors.DuplicateDatabase:
    print(f"Database {db_name} already exists.")
except Exception as e:
    print(f"Error creating database: {e}")
finally:
    cur.close()
    conn.close()
