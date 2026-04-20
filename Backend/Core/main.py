import os
import qrcode
from Block import Block
from authentication import init_db, register, login, voted
from smart_contract import admin_check
from crypto import VoteEncryption, DigitalSignatures
from validation_checker import VoteValidation
from user_vote import get_vote, load_election
from chain import load_blockchain


# Authentication system
init_db()

# Voter receipt
class AddVote:
    def hash_output(self, encrypted_vote, signature, public_key, election_id):

        blockchain = load_blockchain()
        previous_hash = blockchain[-1].block_hash
        index = len(blockchain)

        new_block = Block(index, previous_hash, encrypted_vote, election_id, signature, public_key, vote_time=None)

        print("Here is your hash receipt, you can use this to validate your vote at the end:",
              new_block.block_hash)

        url = new_block.block_hash.strip()
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()

        print("Here is your QR code which displays your verification receipt")
        img.show()

        os.makedirs("qr_receipts", exist_ok=True)
        img.save(f"qr_receipts/{new_block.block_hash}.png")

        new_block.export_to_json()


# Voting loop
if __name__ == "__main__":
    while True:
        print("\n--- Welcome to the E-Voting System ---")
        print("1. Register")
        print("2. Login")
        print("3. Exit ")
        print("4. Admin")

        choice = input("Select option: ").strip()

        if choice == "1":
            register()
            continue

        elif choice == "2":
            user_id, username, has_voted, is_admin = login()

            if user_id is None:
                print("Please login to continue.")
                continue

            if has_voted:
                print("\nYou have already voted.")
                print("You can verify your vote using your receipt.")

                vote_validation = VoteValidation()
                receipt = input("Please enter your vote receipt or scan QR code: ")
                vote_validation.VerifyHash(receipt)
                continue

            election_data = load_election()

            if election_data.get("status") == "closed":
                print("Election has ended. Voting is closed.")

                verify = input("Do you want to verify a vote? (y/n): ").strip().lower()
                if verify == "y":
                    vote_validation = VoteValidation()
                    receipt = input("Enter your receipt: ")
                    vote_validation.VerifyHash(receipt)
                continue

            vote = get_vote()
            encrypted_vote = VoteEncryption.encrypt_vote(vote)

            #  RSA signing before encrypted vote is added to block
            ds = DigitalSignatures()
            signature = ds.sign(username, encrypted_vote)

            public_key = ds.get_public_key(username)

            if not public_key or not ds.verify(encrypted_vote, signature, public_key):
                print("Signature verification failed. Vote rejected.")
                continue

            election_id = election_data.get("election_id", election_data["elec_name"])

            print("You have voted for:", vote)

            AddVote().hash_output(encrypted_vote, signature, public_key, election_id)
            voted(user_id)

            print("\nYou have successfully voted.")
            print("You are now logged out.")
            continue

        elif choice == "3":
            break

        elif choice == "4":
            admin_check()

        else:
            print("Invalid choice. Please select a valid option.")
            continue
