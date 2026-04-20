import hashlib
import datetime
import os
import json
import base64


class Block:
    def __init__(self, index, previous_hash, encrypted_vote, election_id, signature, public_key, vote_time=None):

        self.index = index
        self.vote_time = vote_time if vote_time else datetime.datetime.utcnow().isoformat()
        self.encrypted_vote = encrypted_vote
        self.signature = signature
        self.public_key = public_key
        self.previous_hash = previous_hash
        self.election_id = election_id
        self.block_hash = self.calculate_hash()

    # Calculating hash from input data
    def calculate_hash(self):
        vote_string = self.encrypted_vote.hex() if isinstance(self.encrypted_vote, bytes) else self.encrypted_vote
        sig_string = self.signature.hex() if self.signature else ""
        pk_string = self.public_key if self.public_key else ""

        string_to_hash = (str(self.index) + self.vote_time + vote_string + sig_string + pk_string +
        self.previous_hash + self.election_id)

        return hashlib.sha256(string_to_hash.encode()).hexdigest()

    def is_valid_hash(self):
        return self.calculate_hash() == self.block_hash

    # Persisting blockchain
    def export_to_json(self, folder="blockchain_backup"):
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.join(folder, f"block_{self.index}.json")

        with open(filename, "w") as f:
            json.dump({
                "index": self.index,
                "vote_time": self.vote_time,
                "encrypted_vote": base64.b64encode(self.encrypted_vote).decode(),
                "signature": self.signature.hex() if self.signature else "",
                "public_key": self.public_key,
                "previous_hash": self.previous_hash,
                "election_id": self.election_id,
                "block_hash": self.block_hash
            }, f)

    # Loading blockchain from JSON
    def load_from_json(filename):
        with open(filename, "r") as f:
            data = json.load(f)

        encrypted_vote = base64.b64decode(data["encrypted_vote"])
        signature = bytes.fromhex(data["signature"]) if data.get("signature") else None

        block = Block(index=data["index"], previous_hash=data["previous_hash"],
        encrypted_vote=encrypted_vote,election_id=data.get("election_id",
        "legacy"), signature=signature, public_key=data["public_key"], vote_time=data["vote_time"])

        block.block_hash = data["block_hash"]
        return block