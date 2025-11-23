import sqlite3

conn = sqlite3.connect('ffz.db')
cursor = conn.cursor()

# Update alembic version to the migration we have on host
cursor.execute("UPDATE alembic_version SET version_num = '1234567890ab'")
conn.commit()

print("✓ Alembic version updated to: 1234567890ab")

# Verify
cursor.execute('SELECT * FROM alembic_version')
version = cursor.fetchone()
print(f"✓ Current version confirmed: {version[0]}")

conn.close()
