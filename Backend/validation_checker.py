from Main import blockchain, validate_chain

def validation_check():
    if validate_chain(blockchain):
        print("Blockchain is valid")
    else:
        print("Blockchain is invalid")

if __name__=="__Main__":
    validation_check()