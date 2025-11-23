import sqlite3

conn = sqlite3.connect('ffz.db')
cursor = conn.cursor()

cursor.execute('SELECT email, is_verified, is_active FROM users WHERE email = "test@ffz.com"')
result = cursor.fetchone()

if result:
    print(f'✓ User found: {result[0]}')
    print(f'  Verified: {result[1]}')
    print(f'  Active: {result[2]}')
else:
    print('✗ User NOT found')

conn.close()
