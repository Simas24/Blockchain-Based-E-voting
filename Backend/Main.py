import json
import time
import hashlib
import os
import sqlite3
import qrcode
from cryptography.fernet import Fernet
from user_vote import get_vote
from Block import Block, verify_signature
from trancount import TransactionCount
from smart_contract import VoteCounter
from validation_checker import verify_vote
from authentication import init_db, register, login, voted
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization


# Storing encryption key or generating a new one and saving it
KEY_FILE = "secret.key"

if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        ENCRYPTION_KEY = f.read()
else:
    ENCRYPTION_KEY = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(ENCRYPTION_KEY)

cipher = Fernet(ENCRYPTION_KEY)


# Encrypt vote before adding to blockchain
def encrypt_vote(vote: str) -> bytes:
    return cipher.encrypt(vote.encode())

# Creating the initial (genesis block)
def create_genesis_block():
    # index = 0, previous_hash = 0, placeholder to start blockchain
    genesis = Block(0, "0", "WUCUIYIRBESA", signature=None)

# Save to blockchain_backup immediately
    genesis.export_to_json()
    return genesis


# Importing election info from smart contract
with open("election.json", "r") as f:
    data = json.load(f)

elec_name = data["elec_name"]
candidates = data["candidates"]

# Create vote counter (smart contract)
counter = VoteCounter(candidates)



# Initialize blockchain

blockchain = []

backup_folder = "blockchain_backup"
if os.path.exists(backup_folder) and os.listdir(backup_folder):
    # Load all block JSON files sorted by index
    files = sorted(os.listdir(backup_folder), key=lambda x: int(x.split("_")[1].split(".")[0]))
    for file in files:
        blockchain.append(Block.load_from_json(os.path.join(backup_folder,  file)))
else:
    # No backup found, create genesis block
    blockchain = [create_genesis_block()]

transaction_counter = TransactionCount()

#Authentication System
init_db()

def add_vote(encrypted_vote, signature):
    # Find previous hash
    previous_hash = blockchain[-1].block_hash

    # Assign index based on current chain lengh
    index = len(blockchain)

    # Create new block
    new_block = Block(index, previous_hash, encrypted_vote, signature)

    # Add block to blockchain
    blockchain.append(new_block)
    print("Here is your hash receipt, you can use this to validate your vote at the end:", new_block.block_hash)

    # Create, display & save qr code
    url = (new_block.block_hash) .strip()
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    print("Here is your QR code which displays you verification receipt")
    img.show()
    img.save(f"qr_receipts/{new_block.block_hash}.png")

    # Increment transaction count
    transaction_counter.increment()
    print(f"Vote added. Total transactions so far: {transaction_counter.get_count()}")

    # Backup this block as JSON
    new_block.export_to_json()


def validate_chain(chain):
    # Checks if chain is valid
    for i in range(1, len(chain)):
        current_block = chain[i]
        previous_block = chain[i - 1]

        # Check previous_hash link
        if current_block.previous_hash != previous_block.block_hash:
            return False

        # Check block hash integrity
        if current_block.block_hash != current_block.calculate_hash():
            return False

        # Verify signature if present
        if current_block.signature:

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username, public_key FROM users")
            users = cursor.fetchall()
            conn.close()

            valid = False
            for username, public_key_pem in users:
                if verify_signature(current_block.encrypted_vote, current_block.signature, public_key_pem):
                    valid = True
                    break
            if not valid:
                print(f"Invalid signature detected in block {current_block.index}")
                return False

        # Check sequential index
        if current_block.index != previous_block.index + 1:
            return False

    return True

if __name__ == "__main__":
    # Voting loop
    while True:
        print("\n--- Welcome to the E-Voting System ---")
        print("1. Register")
        print("2. Login")
        print("3. Exit and Show Results")

        choice = input("Select option: ").strip()

        if choice == "1":
            register()
            continue

        elif choice == "2":
            user_id, username, has_voted, is_admin = login()

            if user_id is None:
                print("Please login to continue.")
                continue

            # When user already voted
            if has_voted:
                print("\nYou have already voted.")
                print("You can verify your vote using your receipt.")
                verify_vote(blockchain)
                continue

            # Refuse vote after an election has been closed
            with open("election.json", "r") as f:
                election_data = json.load(f)

            if election_data.get("status") == "closed":
                print("Election has ended. Voting is closed.")
                continue

            # If user has not voted, allow voting
            vote = get_vote()

            # Smart contract auto-tally (plaintext vote)
            counter.add_vote(vote)

            # Encrypt vote
            encrypted_vote = encrypt_vote(vote)

            # Load voter's private key
            with open(f"keys/{username}_private.key", "rb") as f:
                private_key_bytes = f.read()
            private_key = serialization.load_pem_private_key(private_key_bytes, password=None)

            # Sign the encrypted vote
            signature = private_key.sign(
                encrypted_vote,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            print("Plain vote:", vote)
            print("Encrypted vote:", encrypted_vote)

            # Store ONLY encrypted vote & signature on blockchain
            add_vote(encrypted_vote, signature)

            # Mark user as already voted
            voted(user_id)

            print("\nYou have successfully voted.")
            print("You are now logged out.")
            print("You can log in anytime to verify your vote using your receipt.")

            # After voting, return to main menu
            continue

        elif choice == "3":
            print("\nCurrent tally is:")
            counter.display_counts()

            if validate_chain(blockchain):
                print("Blockchain integrity verified.")
            else:
                print("Warning: Blockchain integrity failed!")

            continue

        elif choice == "4" and is_admin:
            # Admin chooses to end election
            confirm = input("Are you sure you want to end this election? (y/n): ").strip().lower()
            if confirm == "y":
                # Update election status in JSON
                with open("election.json", "r") as f:
                    data = json.load(f)
                data["status"] = "closed"
                with open("election.json", "w") as f:
                    json.dump(data, f)

                # Output the winner of the election
                print("Election has been ended.")
                print("Final results:")
                counter.display_counts()
            else:
                print("Returning to menu.")
            continue

        else:
            print("Invalid choice. Please select a valid option.")
            continue









