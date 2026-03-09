import sqlite3
import hashlib
import re
import datetime
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

DATABASE = "users.db"

def lock_time(failed_attempts):
    if failed_attempts >= 7:
        return 120  # 2 hours (in minutes)
    elif failed_attempts >= 5:
        return 20   # 20 minutes
    elif failed_attempts >= 3:
        return 5    # 5 minutes
    return 0

# Database Setup
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Users table includes normal user, admin & lock out rules
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "username TEXT UNIQUE NOT NULL, "
        "password_hash TEXT NOT NULL, "
        "has_voted INTEGER DEFAULT 0, "
        "is_admin INTEGER DEFAULT 0, "
        "failed_attempts INTEGER DEFAULT 0, "
        "lock_until TEXT DEFAULT NULL)"
    )

    conn.commit()
    conn.close()


# Password Hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def valid_password(password):
    if len(password) < 12:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[0-9]", password):
        return False

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\[\]]", password):
        return False

    return True

# New Voter/Admin Registration
def register(admin=False):
    username = input("Enter username: ")
    while True:
        password = input("Enter password: ")

        if valid_password(password):
            break
        else:
            print("Password must be at least 12 characters long, contain at least: 1 uppercase letter, 1 number & 1 special character")

    password_hash = hash_password(password)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username, password_hash, 1 if admin else 0)
        )
        conn.commit()
        if admin:
            print("Admin registration successful.")
        else:
            print("Registration successful.")
    except sqlite3.IntegrityError:
        print("Username already exists.")

    conn.commit()

    # Ensure folder exists
    os.makedirs("keys", exist_ok=True)

    # Generate RSA key pair for the voter
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Serialize keys
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Save private key locally
    with open(f"keys/{username}_private.key", "wb") as f:
        f.write(priv_bytes)

    # Save public key in DB (add column if needed)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN public_key TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("UPDATE users SET public_key=? WHERE username=?",
                   (pub_bytes.decode('utf-8'), username))
    conn.commit()
    conn.close()





# Existing voter/admin login
def login(admin_required=False):
    username = input("Username: ")
    password = input("Password: ")
    password_hash = hash_password(password)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # fetch user by username only (needed for lockout logic)
    cursor.execute(
        "SELECT id, password_hash, has_voted, is_admin, failed_attempts, lock_until "
        "FROM users WHERE username=?",
        (username,)
    )
    user = cursor.fetchone()

    if user:
        user_id, stored_hash, has_voted, is_admin, failed_attempts, lock_until = user

        # check if locked
        if lock_until:
            lock_time_obj = datetime.datetime.fromisoformat(lock_until)
            if datetime.datetime.utcnow() < lock_time_obj:
                print(f"Account locked until {lock_time_obj}.")
                conn.close()
                return None if admin_required else (None, None, None, None)

        # check password
        if stored_hash == password_hash:

            # reset failed attempts on success
            cursor.execute(
                "UPDATE users SET failed_attempts=0, lock_until=NULL WHERE id=?",
                (user_id,)
            )
            conn.commit()
            conn.close()

            if admin_required:
                if is_admin:
                    print("Admin login successful.")
                    return user_id
                else:
                    print("Access denied.")
                    return None
            else:
                print("Login successful.")
                return user_id, username, has_voted, is_admin

        else:
            # handle failed attempt
            failed_attempts += 1
            minutes = lock_time(failed_attempts)

            if minutes > 0:
                lock_until_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
                cursor.execute(
                    "UPDATE users SET failed_attempts=?, lock_until=? WHERE id=?",
                    (failed_attempts, lock_until_time.isoformat(), user_id)
                )
                print(f"Too many failed attempts. Account locked for {minutes} minutes.")
            else:
                cursor.execute(
                    "UPDATE users SET failed_attempts=? WHERE id=?",
                    (failed_attempts, user_id)
                )
                print("Invalid credentials.")

            conn.commit()
            conn.close()
            return None if admin_required else (None, None, None, None)

    else:
        print("Invalid credentials.")
        conn.close()
        return None if admin_required else (None, None, None, None)


# Mark User As Voted
def voted(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET has_voted=1 WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()
