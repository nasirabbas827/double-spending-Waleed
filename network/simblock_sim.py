import simpy
import random
from blockchain.blockchain import Blockchain, Transaction

class Node:
    def __init__(self, name, env, blockchain, hash_rate, delay):
        self.name = name
        self.env = env
        self.blockchain = blockchain
        self.hash_rate = hash_rate
        self.delay = delay
        self.received_transactions = []

    def receive_transaction(self, tx):
        if tx.id not in [t.id for t in self.received_transactions]:
            self.received_transactions.append(tx)
            self.blockchain.add_transaction(tx)

class BlockchainNetworkSimulator:
    def __init__(self):
        self.env = simpy.Environment()
        self.blockchain = Blockchain(difficulty=2)
        self.nodes = []
        self.create_nodes()

    def create_nodes(self):
        names = ['Node 1', 'Node 2', 'Node 3' , 'Nasir' , 'Abbas']
        for name in names:
            hash_rate = random.uniform(0.1, 0.5)
            delay = random.uniform(1, 3)
            node = Node(name, self.env, self.blockchain, hash_rate, delay)
            self.nodes.append(node)

    def broadcast_transaction(self, tx):
        for node in self.nodes:
            self.env.process(self.deliver_transaction(node, tx))
        self.env.run()

    def deliver_transaction(self, node, tx):
        yield self.env.timeout(node.delay)
        node.receive_transaction(tx)

    def get_node_by_name(self, name):
        for node in self.nodes:
            if node.name == name:
                return node
        return None
