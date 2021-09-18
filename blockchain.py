import hashlib
import json
from time import time 
from flask import Flask, jsonify, request 
from uuid import uuid4
from flask.wrappers import Response
from urllib.parse import urlparse 
import requests
from werkzeug.wrappers import response 


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

        self.nodes = set()

    def register_node(self, address):
        """
        add a new node to the list of nodes
        :param address: Address of node. eg. 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(last_block)
            print(block)
            print("\n--------\n")
            
            #check that the hash of the previous block is correct

            if block["previous_hash"] != self.hash(last_block):
                print("Previous hash does not match")
                return False

            if not self.valid_proof(block):
                print("Block proof of work is invalid")
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflict(self):
        """
        This is our consensus algorith, it resolves conflicts
        by replaceing our chain with the longest one in the network
        return: True if our chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None
        #We're only looking for chains Longer than ours
        max_length = len(self.chain)
        #Grab and verify the chains from all the other nodes in our netwrok
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                #check if the lentgh is longer and the cain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        #replace our chain if we're discovered a new valid chain, Longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

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

    # First the register_nodes() function (this connection is NOT bi-directional): 
@app.route('/nodes/register', methods = ['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message' : 'New nodes have been added',
        'total_nodes' : list(blockchain.nodes)
    }
    return jsonify(response), 201

    # Then the consensus() function:

@app.route('/nodes/resolve', methods = ['GET'])
def consesus():
    replaced = blockchain.resolve_conflict()

    if replaced:
        response = {
            'message' : 'Our chain was replaced',
            'new_chain' : blockchain.chain
        }
    
    else:
        response = {
            'message' : 'Our chain is authoritative',
            'chain' : blockchain.chain
        }
    return jsonify(response), 200

#8.	Run the server on port 5000. 

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, 
                        help='port to listen on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
