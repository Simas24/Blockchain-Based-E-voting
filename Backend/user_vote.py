import json

# Load election from file
with open("election.json", "r") as f:
    data = json.load(f)

elec_name = data["elec_name"]
candidates = data["candidates"]

class GenElec:
    def __init__(self, elec_name, candidates):
        self.elec_name = elec_name
        self.candidates = candidates

    def display_candidates(self):
        letter = ord("A")
        for candidate in self.candidates:
            print(f"{chr(letter)}. {candidate}")
            letter += 1

election = GenElec(elec_name, candidates)

def get_vote():
    print(f"\nWelcome to: {election.elec_name}")
    print("Please select the candidate you would like to vote for.")
    print("Enter the alphabetical letter next to their name.\n")
    election.display_candidates()

    vote = input("\nYour choice: ").upper()
    index = ord(vote) - ord("A")
    if 0 <= index < len(election.candidates):
        chosen_candidate = election.candidates[index]
        print(f"You voted for: {chosen_candidate}")
        return chosen_candidate
    else:
        print("Invalid choice. Try again.")
        return get_vote()