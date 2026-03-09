import random
import string
import time
import os
import sqlite3
from Main import register, login, voted, encrypt_vote, add_vote, counter, blockchain
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

# Number of simulated users
NUM_USERS = 50  # adjust to whatever you want for testing
DELAY = 0.05    # delay between each simulated vote (seconds)

# Load candidates from the election.json file
import json
with open("election.json", "r") as f:
    election_data = json.load(f)
candidates = election_data["candidates"]

# Store credentials in memory
registered_users = []

def generate_username(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def generate_password():
    special = "!@#$%^&*()_+-=<>?"
    letters = string.ascii_letters
    digits = string.digits
    all_chars = letters + digits + special

    # Ensure at least 1 uppercase, 1 number, 1 special
    pwd = random.choice(string.ascii_uppercase) + random.choice(digits) + random.choice(special)
    pwd += ''.join(random.choices(all_chars, k=9))  # total 12 chars
    pwd_list = list(pwd)
    random.shuffle(pwd_list)
    return ''.join(pwd_list)

def simulate_user(i):
    # Generate unique random credentials
    username = generate_username()
    password = generate_password()

    # Register the user
    register(username=username, password=password)
    registered_users.append({"username": username, "password": password})

    # Login immediately
    result = login(username=username, password=password)
    if result[0] is None:
        print(f"[ERROR] {username} failed to login")
        return
    user_id, _, has_voted, _ = result

    # Choose random vote
    vote_choice = random.choice(candidates)
    print(f"[{i+1}] {username} voting for {vote_choice}")

    # Update smart contract tally
    counter.add_vote(vote_choice)

    # Encrypt vote
    encrypted_vote = encrypt_vote(vote_choice)

    # Load voter's private key
    with open(f"keys/{username}_private.key", "rb") as f:
        private_key_bytes = f.read()
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)

    # Sign vote
    signature = private_key.sign(
        encrypted_vote,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # Add vote to blockchain
    add_vote(encrypted_vote, signature)

    # Mark user as voted
    voted(user_id)

    # Optional delay to simulate real users
    time.sleep(DELAY)

if __name__ == "__main__":
    print(f"Starting simulation of {NUM_USERS} users voting...\n")
    for i in range(NUM_USERS):
        simulate_user(i)

    print("\nSimulation complete. Total votes tallied in smart contract:")
    counter.display_counts()