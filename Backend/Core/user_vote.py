import json
import os
from election import GenElec


# Importing election data from smart contract
def load_election():
    if not os.path.exists("election.json"):
        return None

    with open("election.json", "r") as f:
        return json.load(f)

# Voter election menu
def get_vote():
        election_data = load_election()
        if not election_data:
            print("No election found.")
            return None

        election = GenElec(election_data["elec_name"], election_data["candidates"])


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

            # Ensuring only valid input is accepted
            if len(vote) != 1:
                print("Please enter ONLY a single letter (A-Z).")
                continue

            # Ensuring a valid alphabetical letter (A-Z) is the vote
            if not vote.isalpha():
                print("Invalid input. Only letters A-Z are allowed.")
                continue

            # Converting letter to candidate index
            index = ord(vote) - ord("A")

            #  Mapping letter to candidate
            if 0 <= index < len(election.candidates):
                chosen_candidate = election.candidates[index]
                print(f"You voted for: {chosen_candidate}")
                return chosen_candidate
            else:
                print("Invalid choice. Please select a valid candidate letter.")

