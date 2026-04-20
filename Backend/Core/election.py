# Generating new election
class GenElec:

    def __init__(self, elec_name, candidates):
        self.elec_name = elec_name
        self.candidates = candidates

    def display_candidates(self):
        letter = ord("A")
        for candidate in self.candidates:
            print(f"{chr(letter)}. {candidate}")
            letter += 1