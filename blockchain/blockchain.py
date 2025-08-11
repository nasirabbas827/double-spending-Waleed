import hashlib
import time
import uuid

class Transaction:
    def __init__(self, sender, receiver, amount):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount
        }

class Block:
    def __init__(self, index, transactions, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = str(self.index) + str(self.timestamp) + str([tx.to_dict() for tx in self.transactions]) + self.previous_hash + str(self.nonce)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self, difficulty=2):
        self.chain = []
        self.transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, [], "0")
        self.chain.append(genesis)

    def add_transaction(self, tx):
        self.transactions.append(tx)

    def mine_block(self):
        if not self.transactions:
            return None
        new_block = Block(len(self.chain), self.transactions, self.chain[-1].hash)
        self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.transactions = []
        return new_block

    def proof_of_work(self, block):
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash = block.compute_hash()

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr.previous_hash != prev.hash:
                return False
            if curr.hash != curr.compute_hash():
                return False
        return True
