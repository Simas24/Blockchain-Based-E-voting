import json
import time
import hashlib
from cryptography.fernet import Fernet
from user_vote import get_vote
from Block import Block
from trancount import TransactionCount
from smart_contract import VoteCounter
from validation_checker import verify_vote


# Encryption key
ENCRYPTION_KEY = Fernet.generate_key()
cipher = Fernet(ENCRYPTION_KEY)


# Encrypt vote before adding to blockchain
def encrypt_vote(vote: str) -> bytes:
    return cipher.encrypt(vote.encode())



# Creating the initial (genesis block)
def create_genesis_block():
    # index = 0, previous_hash = 0, placeholder to start blockchain
    return Block(0, "0", "WUCUIYIRBESA")



# Importing election info from smart contract
with open("election.json", "r") as f:
    data = json.load(f)

elec_name = data["elec_name"]
candidates = data["candidates"]

# Create vote counter (smart contract)
counter = VoteCounter(candidates)



blockchain = [create_genesis_block()]
transaction_counter = TransactionCount()


def add_vote(encrypted_vote):
    # Find previous hash
    previous_hash = blockchain[-1].block_hash

    # Assign index based on current chain lengh
    index = len(blockchain)

    # Create new block
    new_block = Block(index, previous_hash, encrypted_vote)

    # Add block to blockchain
    blockchain.append(new_block)
    print("Here is your hash recipt, you can use this to validate your vote at the end:", new_block.block_hash)

    # Increment transaction count
    transaction_counter.increment()
    print(f"Vote added. Total transactions so far: {transaction_counter.get_count()}")


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

        # Check sequential index
        if current_block.index != previous_block.index + 1:
            return False

    return True


# Voting loop

try:
    while True:
        vote = get_vote()

        # Smart contract auto-tally (plaintext vote)
        counter.add_vote(vote)

        #  Encrypt vote
        encrypted_vote = encrypt_vote(vote)

        print("Plain vote:", vote)
        print("Encrypted vote:", encrypted_vote)

        # Store ONLY encrypted vote on blockchain
        add_vote(encrypted_vote)

        # Ask voter if they want to verify their vote
        verify_vote(blockchain)

        if validate_chain(blockchain):
            print("Blockchain is valid")
        else:
            print("Blockchain is invalid")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n\nVoting ended by administrator.")
    counter.display_counts()
    print("System shutting down.")










