import hashlib
import datetime
import os
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding



# Signature verification
def verify_signature(vote, signature, public_key_pem):
    public_key = serialization.load_pem_public_key(public_key_pem.encode())

    try:
        public_key.verify(
            signature,
            vote,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False


class Block:
    def __init__(self, index, previous_hash, encrypted_vote, signature, vote_time=None):
        self.index = index
        self.vote_time = vote_time if vote_time else datetime.datetime.utcnow().isoformat()
        self.encrypted_vote = encrypted_vote
        self.signature = signature
        self.previous_hash = previous_hash
        self.block_hash = self.calculate_hash()

    def calculate_hash(self):
        sig_hex = self.signature.hex() if self.signature else ""

        if isinstance(self.encrypted_vote, bytes):
            vote_string = self.encrypted_vote.hex()
        else:
            vote_string = self.encrypted_vote

        string_to_hash = (str(self.index) + self.vote_time + vote_string + sig_hex + self.previous_hash)
        return hashlib.sha256(string_to_hash.encode()).hexdigest()

    def export_to_json(self, folder="blockchain_backup"):
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, f"block_{self.index}.json")
        with open(filename, "w") as f:
            json.dump({
                "index": self.index,
                "vote_time": self.vote_time,
                "encrypted_vote": base64.b64encode(self.encrypted_vote).decode() if isinstance(self.encrypted_vote, bytes) else self.encrypted_vote,
                "signature": self.signature.hex() if self.signature else None,
                "previous_hash": self.previous_hash,
                "block_hash": self.block_hash
            }, f)

    @staticmethod
    def load_from_json(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        encrypted_vote = base64.b64decode(data["encrypted_vote"])
        signature = bytes.fromhex(data["signature"]) if data["signature"] else None
        block = Block(
            index=data["index"],
            previous_hash=data["previous_hash"],
            encrypted_vote=encrypted_vote,
            signature=signature,
            vote_time=data["vote_time"]
        )
        block.block_hash = data["block_hash"]

        return block









