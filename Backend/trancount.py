class TransactionCount:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

    def get_count(self):
        return self.count
    def display_count(self):
        print ("Total transaction so far: {self.count}")
