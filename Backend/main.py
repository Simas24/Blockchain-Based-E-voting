from Block import Block
from trancount import TransactionCount


def create_genesis_block():
    # index = 0, previous_hash = 0, WUCUIYIRBESA is placeholder to start blockchain
    return Block(0, "0", "WUCUIYIRBESA")

blockchain = [create_genesis_block()]
transaction_counter = TransactionCount()

def add_vote(encrypted_vote):

    # Find previous hash
    previous_hash = blockchain[-1].block_hash
    # assign index based on current chain length
    index = len(blockchain)

    # Create new block
    new_block = Block(index, previous_hash, encrypted_vote)

    # Add block to blockchain
    blockchain.append(new_block)
    print("Blockchain is working with no errors:", new_block.block_hash)

    # Increment transaction count
    transaction_counter.increment()
    print(f"Vote added. Total transactions so far: {transaction_counter.get_count()}")

def validate_chain(chain):
    # checks if  chain is valid or not, output in validation_checker.py
    for i in range(1, len(chain)):
        current_block = chain[i]
        previous_block = chain[i - 1]

        # 1. Check previous_hash link
        if current_block.previous_hash != previous_block.block_hash:
            return False

        # 2. Check block hash integrity
        if current_block.block_hash != current_block.calculate_hash():
            return False

        # 3. Check sequential index
        if current_block.index != previous_block.index + 1:
            return False

    return True










