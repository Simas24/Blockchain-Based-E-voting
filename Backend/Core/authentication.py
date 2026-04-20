import sqlite3
import hashlib
import re
import datetime
from crypto import DigitalSignatures

DATABASE = "users.db"
MAX_ATTEMPTS = 5
LOCK_TIME_MINUTES = 5

# Initialise Database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            has_voted INTEGER DEFAULT 0,
            failed_attempts INTEGER DEFAULT 0,
            lock_until TEXT DEFAULT NULL,
            public_key TEXT
        )
        """)

# Password complexity rules
def valid_password(p):
    return (
        len(p) >= 12 and
        re.search(r"[A-Z]", p) and
        re.search(r"[0-9]", p) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\[\]]", p)
    )


def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


def register(admin=False):
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    if not valid_password(password):
        print("Please make sure you password is 12+ characters, has a number, an upper case letter and a special character.")
        return

    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (username, hash_password(password), int(admin))
            )
        DigitalSignatures().generate_keys(username)
        print("User registered.")
    except sqlite3.IntegrityError:
        print("Invalid username or password.")


def login(admin_required=False):
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, password_hash, is_admin, has_voted,
                   failed_attempts, lock_until
            FROM users WHERE username=?
        """, (username,))
        user = cursor.fetchone()

        if not user:
            print("Invalid username or password.")
            return None, None, None, None

        user_id, stored_hash, is_admin, has_voted, attempts, lock_until = user

        # Initialising lockout rules
        if lock_until:
            lock_time = datetime.datetime.fromisoformat(lock_until)
            if datetime.datetime.utcnow() < lock_time:
                print("Account locked. Try later.")
                return None, None, None, None
            conn.execute("UPDATE users SET failed_attempts=0, lock_until=NULL WHERE id=?", (user_id,))

        # Incremental counts for lockout rules
        if hash_password(password) != stored_hash:
            attempts += 1
            if attempts >= MAX_ATTEMPTS:
                lock = (datetime.datetime.utcnow() + datetime.timedelta(minutes=LOCK_TIME_MINUTES)).isoformat()
                conn.execute("UPDATE users SET failed_attempts=?, lock_until=? WHERE id=?", (attempts, lock, user_id))
                print("Account locked.")
            else:
                conn.execute("UPDATE users SET failed_attempts=? WHERE id=?", (attempts, user_id))
                print(f"Invalid login. {MAX_ATTEMPTS - attempts} attempts left.")
            return None, None, None, None

        # Reset counter
        conn.execute("UPDATE users SET failed_attempts=0, lock_until=NULL WHERE id=?", (user_id,))

        if admin_required and not is_admin:
            print("Admin required.")
            return None, None, None, None

        print("Login successful.")
        return user_id, username, has_voted, is_admin

# has_voted marker
def voted(user_id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("UPDATE users SET has_voted=1 WHERE id=?", (user_id,))