import simpy
import random
from blockchain.blockchain import Blockchain, Transaction
import time

class Node:
    def __init__(self, name, env, blockchain, hash_rate, delay):
        self.name = name
        self.env = env
        self.blockchain = blockchain
        self.hash_rate = hash_rate
        self.delay = delay
        self.received_transactions = []
        self.mempool = []

    def receive_transaction(self, tx):
        if tx.id not in [t.id for t in self.received_transactions]:
            self.received_transactions.append(tx)
            if tx not in self.mempool:
                self.mempool.append(tx)
            if tx not in self.blockchain.pending_transactions:
                self.blockchain.add_transaction(tx)
            print(f"[{self.name}] Received transaction: {tx.sender} -> {tx.receiver} (Amount: {tx.amount}, ID: {tx.id}, Timestamp: {tx.timestamp})")
            sender_bal = self.blockchain.get_balance(tx.sender)
            if sender_bal < tx.amount:
                print(f"[{self.name}] Validation failed: Insufficient funds for {tx.sender}")
            else:
                print(f"[{self.name}] Transaction validated successfully.")

    def receive_block(self, block):
        if self.blockchain.validate_and_add_block(block):
            print(f"[{self.name}] Accepted new block {block.index} with hash {block.hash}")
            self.mempool = [tx for tx in self.mempool if tx.id not in [t.id for t in block.transactions]]
        else:
            print(f"[{self.name}] Rejected invalid block.")

    def mine(self):
        if self.blockchain.pending_transactions:
            new_block = self.blockchain.create_block(self.blockchain.pending_transactions[:])
            if self.blockchain.proof_of_work(new_block, self.hash_rate):
                self.blockchain.validate_and_add_block(new_block)
                return new_block
        return None

class BlockchainNetworkSimulator:
    def __init__(self):
        self.env = simpy.Environment()
        self.blockchain = Blockchain(difficulty=2)
        self.nodes = []
        self.create_nodes()

    def create_nodes(self):
        names = ['Node 1', 'Node 2', 'Node 3', 'Node 4', 'Node 5', 'Node 6']
        for name in names:
            hash_rate = random.uniform(0.1, 0.3)
            delay = random.uniform(1, 3)
            node = Node(name, self.env, self.blockchain, hash_rate, delay)
            self.nodes.append(node)

    def broadcast_transaction(self, tx):
        print(f"Broadcasting transaction: {tx.sender} -> {tx.receiver} (Amount: {tx.amount}, ID: {tx.id}, Timestamp: {tx.timestamp})")
        for node in self.nodes:
            self.env.process(self.deliver_transaction(node, tx))
        self.env.run()

    def deliver_transaction(self, node, tx):
        yield self.env.timeout(node.delay)
        node.receive_transaction(tx)

    def broadcast_block(self, block):
        print(f"Broadcasting block {block.index} with hash {block.hash}")
        for node in self.nodes:
            self.env.process(self.deliver_block(node, block))
        self.env.run()

    def deliver_block(self, node, block):
        yield self.env.timeout(node.delay)
        node.receive_block(block)

    def get_node_by_name(self, name):
        for node in self.nodes:
            if node.name == name:
                return node
        return None

    def continuous_mining(self):
        def mining_process(node):
            while True:
                block = node.mine()
                if block:
                    self.broadcast_block(block)
                yield self.env.timeout(random.uniform(5, 15))
        for node in self.nodes:
            self.env.process(mining_process(node))