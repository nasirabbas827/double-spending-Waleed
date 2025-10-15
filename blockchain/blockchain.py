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
        self.pending_transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, [], "0")
        self.proof_of_work(genesis, hash_rate=1.0)
        self.chain.append(genesis)

    def add_transaction(self, tx):
        self.pending_transactions.append(tx)

    def create_block(self, transactions):
        return Block(len(self.chain), transactions, self.chain[-1].hash)

    def mine_block(self):
        if not self.pending_transactions:
            return None
        new_block = self.create_block(self.pending_transactions[:])
        if self.proof_of_work(new_block, hash_rate=1.0):
            self.chain.append(new_block)
            self.pending_transactions = []
            return new_block
        return None

    def proof_of_work(self, block, hash_rate):
        attempts = 0
        max_attempts = int(10000 / max(hash_rate, 0.1))
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash = block.compute_hash()
            attempts += 1
            if attempts > max_attempts:
                return False
        return True

    def validate_and_add_block(self, block):
        if block.previous_hash != self.chain[-1].hash:
            return False
        if block.hash != block.compute_hash():
            return False
        self.chain.append(block)
        self.pending_transactions = [tx for tx in self.pending_transactions if tx.id not in [t.id for t in block.transactions]]
        return True

    def replace_chain(self, new_chain):
        if len(new_chain) > len(self.chain) and self.is_chain_valid(new_chain):
            self.chain = new_chain
            return True
        return False

    def is_chain_valid(self, chain=None):
        check_chain = chain or self.chain
        for i in range(1, len(check_chain)):
            prev = check_chain[i - 1]
            curr = check_chain[i]
            if curr.previous_hash != prev.hash:
                return False
            if curr.hash != curr.compute_hash():
                return False
        return True

    def get_balance(self, address):
        balance = 100
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.receiver == address:
                    balance += tx.amount
        return max(balance, 0)