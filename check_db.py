import sqlite3

conn = sqlite3.connect('ffz.db')
cursor = conn.cursor()

print("=== Users Table Columns ===")
cursor.execute('PRAGMA table_info(users)')
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print("\n=== Current Alembic Version ===")
cursor.execute('SELECT * FROM alembic_version')
version = cursor.fetchone()
if version:
    print(f"  Current: {version[0]}")
else:
    print("  No version set")

print("\n=== Checking if is_verified column exists ===")
cursor.execute('PRAGMA table_info(users)')
columns = [row[1] for row in cursor.fetchall()]
if 'is_verified' in columns:
    print("  ✓ Column 'is_verified' exists")
else:
    print("  ✗ Column 'is_verified' NOT found")

conn.close()
