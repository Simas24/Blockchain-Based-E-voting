from Block import Block
import os

# Creating first blockchain block (Genesis)
def create_genesis_block():
    genesis = Block(0, "0", b"WUCUIYIRBESA", "genesis", signature=None,
    public_key=None )
    genesis.export_to_json()
    return genesis

# Initialising blockchain
def load_blockchain():

    backup_folder = "blockchain_backup"
    blockchain = []

    if os.path.exists(backup_folder) and os.listdir(backup_folder):
        files = sorted(
            os.listdir(backup_folder),
            key=lambda x: int(x.split("_")[1].split(".")[0])
        )

        for file in files:
            blockchain.append( Block.load_from_json(os.path.join(backup_folder, file)))

    else:
        blockchain = [create_genesis_block()]

    return blockchain

# Validating blockchain integrity
def validate_chain():
    chain = load_blockchain()

    if not chain:
        return False

    for i in range(1, len(chain)):

        if chain[i].previous_hash != chain[i - 1].block_hash:
            print(f"Broken link at block {chain[i].index}")
            return False

        if not chain[i].is_valid_hash():
            print(f"Hash tampering detected at block {chain[i].index}")
            return False

    return True