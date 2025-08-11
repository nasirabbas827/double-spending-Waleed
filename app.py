from flask import Flask, render_template, request
from blockchain.blockchain import Transaction
from network.simblock_sim import BlockchainNetworkSimulator
from attacker.double_spending import AttackerNode
import pandas as pd
import os


app = Flask(__name__)
simulator = BlockchainNetworkSimulator()

@app.route('/')
def index():
    node_data = [
        {"name": node.name, "hash_rate": round(node.hash_rate, 2), "delay": round(node.delay, 2)}
        for node in simulator.nodes
    ]
    return render_template("index.html", nodes=node_data)

@app.route('/transaction/new', methods=["GET", "POST"])
def new_transaction():
    message = None
    if request.method == "POST":
        sender = request.form["sender"]
        receiver = request.form["receiver"]
        amount = float(request.form["amount"])
        tx = Transaction(sender, receiver, amount)
        simulator.broadcast_transaction(tx)
        message = "Transaction broadcasted successfully. Please mine the block to confirm."

    recent_blocks = simulator.blockchain.chain[1:] if len(simulator.blockchain.chain) > 1 else []
    return render_template("transaction.html", message=message, blocks=recent_blocks)

@app.route('/mine')
def mine():
    block = simulator.blockchain.mine_block()
    if block:
        return f"Block {block.index} mined with hash: {block.hash}"
    return "No transactions to mine."

@app.route('/attack', methods=["GET", "POST"])
def attack():
    result = None
    if request.method == "POST":
        hash_rate = float(request.form["attacker_hash_rate"])
        delay = float(request.form["network_delay"])
        attacker = AttackerNode(simulator.blockchain, hash_rate, delay)
        success, reason = attacker.launch_attack()
        result = f"Success: {success} | Reason: {reason}"
    return render_template("attack.html", result=result)

@app.route('/stats')
def stats():
    if not os.path.exists("logs/attack_log.csv"):
        return render_template("stats.html", stats=None)
    df = pd.read_csv("logs/attack_log.csv")
    return render_template("stats.html", stats=df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)