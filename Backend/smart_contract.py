import time
import json

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

        # Highest voted candidate
        top_candidate, top_votes = sorted_counts[0]
        print(f"\nThe candidate with the most votes is: {top_candidate} ({top_votes} votes)\n")

        # Full ranking
        for i, (candidate, count) in enumerate(sorted_counts, start=1):
            print(f"{i}. {candidate}: {count}")



# For admin only

if __name__ == "__main__":
    # Administrator input
    elec_name = input("Enter the election name: ")
    candidates_input = input("Enter candidate names separated by commas: ")
    candidates = candidates_input.split(",")

    election = GenElec(elec_name, candidates)

    print("\nCandidates:")
    election.display_candidates()

    # Save election to file for other scripts
    election_data = {
        "elec_name": election.elec_name,
        "candidates": election.candidates
    }
    with open("election.json", "w") as f:
        json.dump(election_data, f)

    print("\nElection saved! Smart contract session is now running...")

    # Keep admin session alive indefinitely
    while True:
        print("Smart Contract Admin Session Active...")
        time.sleep(5)