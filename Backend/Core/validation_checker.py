import os
import json
import base64
from Block import Block


class VoteValidation:

    # User validation interface
    def validate_vote(self):
        validate = input("Do you want to verify your vote? (y/n): ").strip().lower()

        if validate != "y":
            print("Vote validation skipped.")
            return

        receipt = input("Please enter your vote receipt or scan your QR code: ")
        self.VerifyHash(receipt)

    # Specific hash validation
    def VerifyHash(self, receipt):


        backup_folder = "blockchain_backup"

        if not os.path.exists(backup_folder) or not os.listdir(backup_folder):
            print("No blockchain data found.")
            return

        for filename in sorted(os.listdir(backup_folder),
                               key=lambda x: int(x.split("_")[1].split(".")[0])):

            # Skips Genesis block
            if filename == "block_0.json":
                continue

            with open(os.path.join(backup_folder, filename), "r") as f:
                data = json.load(f)

            encrypted_vote = base64.b64decode(data["encrypted_vote"])
            signature = bytes.fromhex(data["signature"]) if data.get("signature") else None

            block = Block(
                index=data["index"],
                previous_hash=data["previous_hash"],
                encrypted_vote=encrypted_vote,
                election_id=data["election_id"],
                signature=signature,
                public_key=data["public_key"],
                vote_time=data["vote_time"]
            )

            recalculated_hash = block.calculate_hash()

            if recalculated_hash == receipt:
                if recalculated_hash == data["block_hash"]:
                    print("Your vote is valid!")
                else:
                    print("Your vote has been tampered!")
                return

        print("Your vote is invalid.")


