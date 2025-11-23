import sqlite3
from passlib.context import CryptContext

# Create password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = sqlite3.connect('ffz.db')
cursor = conn.cursor()

# Create a test user
email = "test@ffz.com"
password = "password123"
password_hash = pwd_context.hash(password)

try:
    cursor.execute("""
        INSERT INTO users (email, password_hash, is_active, is_verified, language, first_name, last_name)
        VALUES (?, ?, 1, 1, 'en', 'Test', 'User')
    """, (email, password_hash))
    conn.commit()
    print(f"✓ Test user created:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
except sqlite3.IntegrityError:
    print(f"User {email} already exists")
    # Update to make sure they're verified
    cursor.execute("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))
    conn.commit()
    print(f"✓ Updated existing user to verified")
    print(f"  Email: {email}")
    print(f"  Password: {password}")

conn.close()
