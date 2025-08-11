import random
import time
from blockchain.blockchain import Transaction
import csv
import os

class AttackerNode:
    def __init__(self, blockchain, hash_rate, delay):
        self.blockchain = blockchain
        self.hash_rate = hash_rate
        self.delay = delay

    def launch_attack(self):
        tx1 = Transaction("Attacker", "Ali", 50)
        tx2 = Transaction("Attacker", "Self", 50)  # Conflicting TX

        time.sleep(self.delay)

        # Branch 1 (Legit)
        self.blockchain.add_transaction(tx1)
        self.blockchain.mine_block()

        # Branch 2 (Fake) - attacker tries to override previous
        success = False
        reason = ""

        if self.hash_rate > 0.6:
            self.blockchain.add_transaction(tx2)
            self.blockchain.mine_block()
            success = True
            reason = "Attacker outpaced honest nodes with high hash power"
        else:
            reason = "Attacker failed due to low hash power"

        self.log_attack(self.hash_rate, self.delay, success, reason)
        return success, reason

    def log_attack(self, hash_rate, delay, success, reason):
        os.makedirs("logs", exist_ok=True)
        with open("logs/attack_log.csv", mode="a", newline="") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["Hash Rate", "Network Delay", "Success", "Reason"])
            writer.writerow([hash_rate, delay, success, reason])
