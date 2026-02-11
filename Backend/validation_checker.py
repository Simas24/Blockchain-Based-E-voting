
def verify_vote(blockchain):
    verify = input("Do you want to verify your vote? (y/n): ")
    if verify == "y":
        receipt = input("Enter your vote receipt hash: ")
        # Skip genesis block
        found = any(block.block_hash == receipt for block in blockchain[1:])
        if found:
            print("Your vote is valid!")
        else:
            print("Vote not found or tampered!")
    else:
        print("Vote verification skipped.")
