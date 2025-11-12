import time
from blockchain.blockchain import Transaction, Blockchain
import csv
import os
import json
import random

class AttackerNode:
    def __init__(self, honest_blockchain, total_honest_hash, attacker_node_name, victim_node_name, amount, attacker_hash_rate, delay):
        self.honest_blockchain = honest_blockchain
        self.private_chain = Blockchain(difficulty=2)
        self.private_chain.chain = self.honest_blockchain.chain[:]
        self.private_chain.pending_transactions = []
        self.attacker_node_name = attacker_node_name
        self.victim_node_name = victim_node_name
        self.amount = amount
        self.attacker_hash_rate = attacker_hash_rate
        self.total_honest_hash = total_honest_hash
        self.delay = delay

    def launch_attack(self):
        # Capture a single timestamp for both transactions
        current_timestamp = time.time()

        # Create both transactions with the same timestamp
        tx_to_victim = Transaction(self.attacker_node_name, self.victim_node_name, self.amount, current_timestamp)
        tx_to_self = Transaction(self.attacker_node_name, self.attacker_node_name, self.amount, current_timestamp)

        print(f"Attacker initiating double spend at timestamp {current_timestamp}:")
        print(f"Public TX to Victim: {tx_to_victim.sender} -> {tx_to_victim.receiver} (Amount: {tx_to_victim.amount}, ID: {tx_to_victim.id}, Timestamp: {tx_to_victim.timestamp})")
        print(f"Private TX to Self: {tx_to_self.sender} -> {tx_to_self.receiver} (Amount: {tx_to_self.amount}, ID: {tx_to_self.id}, Timestamp: {tx_to_self.timestamp})")

        # Log both transactions with the same timestamp
        os.makedirs("logs", exist_ok=True)
        with open("logs/transaction_log.csv", mode="a", newline="") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["TX ID", "Sender", "Receiver", "Amount", "Timestamp"])
            writer.writerow([tx_to_victim.id, tx_to_victim.sender, tx_to_victim.receiver, tx_to_victim.amount, current_timestamp])
            writer.writerow([tx_to_self.id, tx_to_self.sender, tx_to_self.receiver, tx_to_self.amount, current_timestamp])

        # Broadcast public transaction to the honest network
        self.honest_blockchain.add_transaction(tx_to_victim)
        # Note: Assume simulator.broadcast_transaction is called externally or integrate with simulator

        # Start mining private chain with tx_to_self
        self.private_chain.pending_transactions = [tx_to_self]
        success = self.mine_private_chain()

        # Simulate network delay
        time.sleep(self.delay)

        # Print detailed block data for both chains
        print("\nHonest Chain Blocks:")
        for block in self.honest_blockchain.chain:
            print(f"Block {block.index}:")
            print(f"  Hash: {block.hash}")
            print(f"  Previous Hash: {block.previous_hash}")
            print(f"  Timestamp: {block.timestamp}")
            print(f"  Nonce: {block.nonce}")
            print(f"  Transactions: {[tx.to_dict() for tx in block.transactions]}")

        print("\nPrivate Chain Blocks:")
        for block in self.private_chain.chain:
            print(f"Block {block.index}:")
            print(f"  Hash: {block.hash}")
            print(f"  Previous Hash: {block.previous_hash}")
            print(f"  Timestamp: {block.timestamp}")
            print(f"  Nonce: {block.nonce}")
            print(f"  Transactions: {[tx.to_dict() for tx in block.transactions]}")

        # Prepare chain data for logging
        honest_chain_data = [block.to_dict() for block in self.honest_blockchain.chain]
        private_chain_data = [block.to_dict() for block in self.private_chain.chain]

        reason = ""
        if success:
            self.honest_blockchain.replace_chain(self.private_chain.chain)
            reason = "Private chain longer and replaced honest chain"
            for i in range(1, len(self.private_chain.chain)):
                block = self.private_chain.chain[i]
                print(f"Network accepted attacker block {block.index} with hash {block.hash}")
        else:
            reason = "Failed to mine longer private chain - spend confirmed on honest chain"

        self.log_attack(self.attacker_hash_rate, self.delay, success, reason, honest_chain_data, private_chain_data)
        
        print("\nPost-attack verification across nodes (shared chain):")
        attacker_bal = self.honest_blockchain.get_balance(self.attacker_node_name)
        victim_bal = self.honest_blockchain.get_balance(self.victim_node_name)
        print(f"Attacker balance: {attacker_bal} (kept coins if >=100 on success)")
        print(f"Victim balance: {victim_bal} (received if failed attack)")

        return success, reason

    def mine_private_chain(self):
        blocks_mined = 0
        required_confirmations = 2  # Configurable if needed
        while blocks_mined < required_confirmations:
            new_block = self.private_chain.create_block(self.private_chain.pending_transactions[:])
            if self.private_chain.proof_of_work(new_block, self.attacker_hash_rate):
                self.private_chain.chain.append(new_block)
                self.private_chain.pending_transactions = []
                blocks_mined += 1
                print(f"Attacker mined private block {new_block.index} with hash {new_block.hash}")
            else:
                print(f"Attacker failed to mine private block")
                return False
        prob_success = self.attacker_hash_rate / (self.attacker_hash_rate + self.total_honest_hash)
        print(f"Attack success probability: {prob_success:.2f}")
        return random.random() < prob_success

    def log_attack(self, hash_rate, delay, success, reason, honest_chain, private_chain):
        os.makedirs("logs", exist_ok=True)
        with open("logs/attack_log.csv", mode="a", newline="") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["Hash Rate", "Network Delay", "Success", "Reason", "Honest Chain", "Private Chain"])
            writer.writerow([hash_rate, delay, success, reason, json.dumps(honest_chain), json.dumps(private_chain)])