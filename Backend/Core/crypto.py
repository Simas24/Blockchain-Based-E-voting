import os
from cryptography.fernet import Fernet
import sqlite3
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

DATABASE = "users.db"


class DigitalSignatures:

    def __init__(self):
        os.makedirs("keys", exist_ok=True)

    # Generating & storing keys
    def generate_keys(self, username):
        private_key = rsa.generate_private_key (public_exponent=65537, key_size=2048)

        public_key = private_key.public_key()

        # Save private key locally
        with open(f"keys/{username}_private.key", "wb") as f:
            f.write(private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))

        # Store public key in database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN public_key TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute(
            "UPDATE users SET public_key=? WHERE username=?",
            (public_key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode(), username)
        )

        conn.commit()
        conn.close()

    # Getting public key from DB
    def get_public_key(self, username):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT public_key FROM users WHERE username=?",
            (username,)
        )
        result = cursor.fetchone()

        conn.close()
        return result[0] if result else None

    # Signing data with private key
    def sign(self, username, data):
        with open(f"keys/{username}_private.key", "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )

        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return signature

    # Verifying signature with public key
    def verify(self, data, signature, public_key_pem):
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode()
        )

        try:
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

# Encryption
KEY_FILE = "secret_key"

if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        SECRET_KEY = f.read()
else:
    SECRET_KEY = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(SECRET_KEY)

cipher = Fernet(SECRET_KEY)

class VoteEncryption:


    # Encryption of plaintext vote
    def encrypt_vote(vote: str) -> bytes:
        return cipher.encrypt(vote.encode())


    # Decryption of plaintext vote
    def decrypt_vote(encrypted_vote: bytes) -> str:
        return cipher.decrypt(encrypted_vote).decode()
