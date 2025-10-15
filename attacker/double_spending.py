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
        tx_to_victim = Transaction(self.attacker_node_name, self.victim_node_name, self.amount)
        tx_to_self = Transaction(self.attacker_node_name, self.attacker_node_name, self.amount)

        print(f"Attacker initiating double spend:")
        print(f"Public TX to Victim: {tx_to_victim.sender} -> {tx_to_victim.receiver} (Amount: {tx_to_victim.amount}, ID: {tx_to_victim.id})")
        print(f"Private TX to Self: {tx_to_self.sender} -> {tx_to_self.receiver} (Amount: {tx_to_self.amount}, ID: {tx_to_self.id})")

        # Add public TX and immediately mine on honest chain to confirm spend
        self.honest_blockchain.add_transaction(tx_to_victim)
        public_block = self.honest_blockchain.mine_block()  # Confirm the public TX
        if public_block:
            print(f"Honest network mined block {public_block.index} confirming public TX to victim.")
        
        time.sleep(self.delay)

        self.private_chain.pending_transactions = [tx_to_self]
        success = self.mine_private_chain()

        honest_chain_data = [{"index": b.index, "hash": b.hash, "previous_hash": b.previous_hash, "transactions": [t.to_dict() for t in b.transactions]} for b in self.honest_blockchain.chain]
        private_chain_data = [{"index": b.index, "hash": b.hash, "previous_hash": b.previous_hash, "transactions": [t.to_dict() for t in b.transactions]} for b in self.private_chain.chain]

        reason = ""
        if success:
            self.honest_blockchain.replace_chain(self.private_chain.chain)
            reason = "Private chain longer and replaced honest chain"
            for i in range(1, len(self.private_chain.chain)):
                block = self.private_chain.chain[i]
                print(f"Network accepted attacker block {block.index}")
        else:
            reason = "Failed to mine longer private chain - spend confirmed on honest chain"

        self.log_attack(self.attacker_hash_rate, self.delay, success, reason, honest_chain_data, private_chain_data)
        
        print("Post-attack verification across nodes (shared chain):")
        attacker_bal = self.honest_blockchain.get_balance(self.attacker_node_name)
        victim_bal = self.honest_blockchain.get_balance(self.victim_node_name)
        print(f"Attacker balance: {attacker_bal} (kept coins if >=100 on success)")
        print(f"Victim balance: {victim_bal} (received if failed attack)")

        return success, reason

    def mine_private_chain(self):
        blocks_mined = 0
        required_confirmations = 2
        while blocks_mined < required_confirmations:
            new_block = self.private_chain.create_block(self.private_chain.pending_transactions[:])
            if self.private_chain.proof_of_work(new_block, self.attacker_hash_rate):
                self.private_chain.chain.append(new_block)
                self.private_chain.pending_transactions = []
                blocks_mined += 1
                print(f"Attacker mined private block {new_block.index}")
            else:
                return False
        prob_success = self.attacker_hash_rate / (self.attacker_hash_rate + self.total_honest_hash)
        return random.random() < prob_success

    def log_attack(self, hash_rate, delay, success, reason, honest_chain, private_chain):
        os.makedirs("logs", exist_ok=True)
        with open("logs/attack_log.csv", mode="a", newline="") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["Hash Rate", "Network Delay", "Success", "Reason", "Honest Chain", "Private Chain"])
            writer.writerow([hash_rate, delay, success, reason, json.dumps(honest_chain), json.dumps(private_chain)])