import sqlite3
import hashlib
import re
import datetime

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
                return None if admin_required else (None, None, None)

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
                return user_id, has_voted, is_admin

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
            return None if admin_required else (None, None, None)

    else:
        print("Invalid credentials.")
        conn.close()
        return None if admin_required else (None, None, None)


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
