import hashlib
import datetime

class Block:
    def __init__(self, index,previous_hash, encrypted_vote):
        self.index = index
        self.vote_time = datetime.datetime.utcnow().isoformat()
        self.encrypted_vote = encrypted_vote
        self.previous_hash = previous_hash
        self.block_hash = self.calculate_hash()


    def calculate_hash(self):
        string_to_hash =str(self.index) + self.vote_time + self.encrypted_vote + self.previous_hash
        return hashlib.sha256(string_to_hash.encode()).hexdigest()








