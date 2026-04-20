import sqlite3
import json
import time
import os
from authentication import login, register, init_db, DATABASE
from crypto import VoteEncryption, DigitalSignatures
from chain import validate_chain, load_blockchain
from user_vote import load_election
from election import GenElec

init_db()



class VoteCounter:

    def __init__(self, candidates=None):
        self.candidates = candidates if candidates else []
        self.counts = {candidate: 0 for candidate in self.candidates}

    # Extracts votes from blockchain & announces winner
    def tally_votes(self, election_id):

        time.sleep(1)
        ds = DigitalSignatures()
        blockchain_data = load_blockchain()

        if not validate_chain():
            print("Blockchain validation failed. Tally aborted.")
            return


        for block in blockchain_data:

            if block.index == 0:
                continue

            if block.election_id != election_id:
                continue

            if not block.encrypted_vote:
                continue

            if not ds.verify(block.encrypted_vote, block.signature, block.public_key):
                print(f"Invalid signature at block {block.index}. Tally aborted.")
                return
            try:
                decrypted_vote = VoteEncryption.decrypt_vote(block.encrypted_vote)
            except Exception:
                print(f"Decryption error at block {block.index}. Skipping block.")
                continue

            if decrypted_vote not in self.counts:
                self.counts[decrypted_vote] = 0

            self.counts[decrypted_vote] += 1

        sorted_counts = sorted(self.counts.items(), key=lambda x: x[1], reverse=True)

        print("\n--- Election Results ---")
        for candidate, count in sorted_counts:
            print(f"{candidate}: {count}")

        if sorted_counts:
            max_votes = sorted_counts[0][1]
            winners = [candidate for candidate, count in sorted_counts if count == max_votes]

            if len(winners) == 1:
                print(f"\n Winner: {winners[0]} with {max_votes} votes!")
            else:
                print(f"\n It's a tie between: {', '.join(winners)} with {max_votes} votes each!")

# Checks for existing admin if N/A asks to log in as admin
def admin_check():
    init_db()

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin=1")
    admin_count = cursor.fetchone()[0]
    conn.close()

    if admin_count == 0:
        print("No admin account found. Creating the first admin...")
        register(admin=True)

    print("\nAdmin login required.")
    user_id, username, has_voted, is_admin = login(admin_required=True)

    if user_id is None or is_admin == 0:
        print("Access denied. Returning to main menu.")
        return

    print("Admin authenticated successfully.")

    # Admin menu loop
    while True:
        print("\n--- Smart Contract Administrator Panel ---")
        print("1. Create Election")
        print("2. Add Core Admin")
        print("3. End Running Election")
        print("4. Exit")

        choice = input("Select option: ").strip()

        if choice == "4":
            break

        if choice == "1":
            elec_name = input("Enter election name: ")
            candidates_input = input("Enter candidate names separated by commas: ")
            candidates = [c.strip() for c in candidates_input.split(",")]

            election = GenElec(elec_name, candidates)
            print("\nCandidates:")
            election.display_candidates()

            election_data = {
                "elec_name": election.elec_name,
                "election_id": str(time.time()),
                "candidates": election.candidates,
                "status": "running"
            }
            with open("election.json", "w") as f:
                json.dump(election_data, f)

            print("\nElection saved! Smart contract session is now running...")
            return

        elif choice == "2":
            register(admin=True)
            print("Core admin created successfully.")

        elif choice == "3":
            if not os.path.exists("election.json"):
                print("No election found.")
                continue

            with open("election.json", "r") as f:
                data = json.load(f)

            if data.get("status") == "closed":
                print("Election is already closed.")
                continue

            confirm = input("Are you sure you want to end this election? (y/n): ").strip().lower()
            if confirm != "y":
                print("Returning to admin panel.")
                continue

            data["status"] = "closed"
            with open("election.json", "w") as f:
                json.dump(data, f)
            print("Election has been ended.")



            data = load_election()

            if not data:
                print("No election found.")
                return

            election_id = data.get("election_id", data["elec_name"])
            counter = VoteCounter(data["candidates"])
            counter.tally_votes(election_id)

