import time
import json
import sqlite3
from authentication import init_db, login, register

DATABASE = "users.db"


class GenElec:
    def __init__(self, elec_name, candidates):
        self.elec_name = elec_name
        self.candidates = candidates

    def display_candidates(self):
        letter = ord("A")
        for candidate in self.candidates:
            print(f"{chr(letter)}. {candidate}")
            letter += 1


class VoteCounter:
    def __init__(self, candidates):
        # initialise vote counts to 0
        self.counts = {candidate: 0 for candidate in candidates}

    def add_vote(self, candidate):
        if candidate in self.counts:
            self.counts[candidate] += 1   # n = n + 1


    def display_counts(self):
        print("\n--- Final Vote Count ---")

        # Sort candidates by vote count (descending)
        sorted_counts = sorted(
            self.counts.items(),
            key=lambda item: item[1],
            reverse=True
        )

        # Check for draw
        top_votes = sorted_counts[0][1]
        top_candidates = [candidate for candidate, count in sorted_counts if count == top_votes]

        if len(top_candidates) > 1:
            print(f"\nThere is a draw between: {', '.join(top_candidates)} ({top_votes} votes each)\n")
        else:
            print(f"\nThe candidate with the most votes is: {top_candidates[0]} ({top_votes} votes)\n")

        # Full ranking
        for i, (candidate, count) in enumerate(sorted_counts, start=1):
            print(f"{i}. {candidate}: {count}")


# For admin only

if __name__ == "__main__":

    # Initialize database
    init_db()

    # Check if any admin exists
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin=1")
    admin_count = cursor.fetchone()[0]
    conn.close()

    # Create first admin if none exists
    if admin_count == 0:
        print("No admin account found.")
        print("Create the first admin account.")
        register(admin=True)

    # Require admin login
    print("\nAdmin login required to start smart contract.")
    admin_id = login(admin_required=True)

    if admin_id is None:
        print("Access denied. Exiting.")
        exit()

    print("\nAdmin authenticated successfully.\n")

    while True:
        print("\n--- Smart Contract Admin Panel ---")
        print("1. Create Election")
        print("2. Add New Admin")
        print("3. End Running Election")
        print("4. Exit")

        choice = input("Select option: ").strip()

        # Administrator creates election
        if choice == "1":
            # Administrator input
            elec_name = input("Enter the election name: ")
            candidates_input = input("Enter candidate names separated by commas: ")
            candidates = [c.strip() for c in candidates_input.split(",")]

            election = GenElec(elec_name, candidates)

            print("\nCandidates:")
            election.display_candidates()

            # Save election to file for other scripts
            election_data = {
                "elec_name": election.elec_name,
                "candidates": election.candidates,
                "status": "running"
            }

            with open("election.json", "w") as f:
                json.dump(election_data, f)

            print("\nElection saved! Smart contract session is now running...")

            # Keep admin session alive indefinitely
            while True:
                print("Smart Contract Admin Session Active...")
                time.sleep(5)

        # Existing admin options
        elif choice == "3":

            with open("election.json", "r") as f:
                data = json.load(f)

            if data.get("status") == "closed":
                print("Election is already closed.")
                continue

            confirm = input("Are you sure you want to end this election? (y/n): ").strip().lower()

            if confirm == "y":
                data["status"] = "closed"

                with open("election.json", "w") as f:
                    json.dump(data, f)

                print("Election has been ended.")
                print("Final results:")

                break

            else:
                print("Returning to admin panel.")
                continue

        elif choice == "4":
            print("Exiting smart contract.")
            break

        else:
            print("Invalid option.")