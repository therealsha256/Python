import hashlib
import json
from time import time 
from flask import Flask, jsonify, request 
from uuid import uuid4
from flask.wrappers import Response

#instantiate our node
app = Flask(__name__)

#generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.pending_transactions = []

        #create the genesis block
        self.new_block(previous_hash = '1', proof = 100)

    def new_block(self, proof, previous_hash = None):
        #create a new Block & adds it to the chain. 
        """
        Create a new Block in the blockchain
        :param proof:    <int> The Proof given by the Proof of Work algorithm
        :param previous_hash:    (Optional) <str> Hash of the previous block
        :return:    <dict> New block
        """
       
        block = {
            'index'    : len(self.chain) + 1,
            'timestamp'     : time(),
            'transactions'    : self.pending_transactions,
            'proof'    : proof,
            'previous_hash'    : previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions
        self.pending_transactions = []

        self.chain.append(block)
        return block
        #pass

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go in+to the next mined block
        :param sender:    <str> Address of the sender
        :param recipient:    <str> Address of the Recipient
        :param amount:    <int> Amount
        :return: <int>    The index of the Block that will hold this transaction     
        """
        self.pending_transactions.append({
            'sender'    : sender,
            'recipient' : recipient,
            'amount'    : amount
        })
        return self.last_block['index'] + 1


    @staticmethod
    def hash(block):
        # hashes a block
        """
        Creates a SHA-256 hash of a Block
        :param block:    <dict> Block
        :return:    <str>
        """
        #we must make sure that the dictionary is ordered, or we will have inconsistent hashes
        block_string = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(block_string).hexdigest()
        #pass

    # 13.	Now the implementation of basic proof-of-work algorithm 
    # by adding the following methods to our Blockchain class: 

    @staticmethod
    def proof_of_work(block):
        """
        Proof-of-Work algorithm.
        Iterate the "proof" field until the conditions are satisfied.
        :param block: <dict>
        """
        while not Blockchain.valid_proof(block):
            block["proof"] += 1

    # 14.	Proof of work method has been implemented. 
    # Now we need a condition for validating the proof. 
    # To adjust the difficulty of the algorithm, 
    # we could modify the number of leading zeroes. 
    # But 4 is enough. You’ll find out that the addition of a single leading zero makes a huge difference
    # to the time required to find a solution. 

    @staticmethod
    def valid_proof(block):
        """
        The Proof-of-Work conditions.
        CHeck if the hash of the block start with 4 zeroes.
        higher difficulty == more zeroes, lower diff == less.
        :param bolck: <dict>
        """
        return Blockchain.hash(block) [:4] == "0000"

        
    @property
    def last_block(self):
        #hashes a block
        
        return self.chain[-1]
        #pass

# 2.	Firstly, we instantiate our node. 
# 3.	Then create a random name for our node. 
# 4.	And instantiate the Blockchain class. 




#instance the Blockchain
blockchain = Blockchain()               #check for correct indentation

#5.	Create the /mine endpoint, which is a GET request. 
# @app.route('/mine', methods = ["GET"])
# def mine():
#     return "We will mine a new block"

#6.	Create the /transactions/new endpoint, which is a POST request, 
# since we’ll be sending data to it. 
# @app.route('/transactions/new', methods = ["POST"])
# def new_transaction():
#     return "We will add a new transaction"

#7.	Create the /chain endpoint, which returns the full blockchain.
@app.route('/chain', methods = ["GET"])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }   
    return jsonify(response), 200

#Enter new transaction end point
@app.route('/transactions/new', methods = ["POST"])
def new_transaction():
    values = request.get_json()

    if not values:
        return "Missing body", 400

    required = ["sender", "recipient", "amount"]

    if not all(k in values for k in required):
        return "Missing values", 400

    index = blockchain.new_transaction(values["sender"], values["recipient"], values["amount"])

    response = {"message": f"transaction will be added to clock {index}"}
    return jsonify(response), 201

#implement the mine() function
@app.route('/mine', methods = ["GET"])
def mine():
    # Add our mining reward
    # sender "0" means new coins
    blockchain.new_transaction(
        sender = "0",
        recipient = node_identifier, 
        amount = 1
    )

    #make the new block and mine it
    block = blockchain.new_block(0)
    blockchain.proof_of_work(block)

    response = {
        "message"    : "New block mined",
        "index"    : block["index"],
        "transactions"    : block["transactions"],
        "proof"    : block["proof"],
        "previous_hash"    : block["previous_hash"]
    }

    return jsonify(response), 200


#8.	Run the server on port 5000. 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
