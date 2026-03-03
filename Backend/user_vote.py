import json
from smart_contract import GenElec

# Load election from file
with open("election.json", "r") as f:
    data = json.load(f)

elec_name = data["elec_name"]
candidates = data["candidates"]


election = GenElec(elec_name, candidates)

def get_vote():
        print(f"\nWelcome to: {election.elec_name}")
        print("Please select the candidate you would like to vote for.")
        print("Enter the alphabetical letter next to their name.\n")
        election.display_candidates()

        while True:
            vote = input("\nYour choice: ").strip().upper()

            # Initiating mandatory field to avoid empty votes
            if not vote:
                print("Input is required. Please enter a letter A-Z.")
                continue

            # Ensuring vote is exactly one character, reducing risk of tampering
            if len(vote) != 1:
                print("Please enter ONLY a single letter (A-Z).")
                continue

            # Ensuring a valid alphabetical letter (A-Z) is the vote
            if not vote.isalpha():
                print("Invalid input. Only letters A-Z are allowed.")
                continue

            # Convert letter to candidate index
            index = ord(vote) - ord("A")

            #  Mapping letter to candidate
            if 0 <= index < len(election.candidates):
                chosen_candidate = election.candidates[index]
                print(f"You voted for: {chosen_candidate}")
                return chosen_candidate
            else:
                print("Invalid choice. Please select a valid candidate letter.")
