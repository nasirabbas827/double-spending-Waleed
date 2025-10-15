from flask import Flask, render_template, request, send_file
from blockchain.blockchain import Transaction
from network.simblock_sim import BlockchainNetworkSimulator
from attacker.double_spending import AttackerNode
import pandas as pd
import os
import csv
import time
import random
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
simulator = BlockchainNetworkSimulator()
total_honest_hash = sum(node.hash_rate for node in simulator.nodes)
node_names = [node.name for node in simulator.nodes]

@app.route('/')
def index():
    node_data = [
        {"name": node.name, "hash_rate": round(node.hash_rate, 2), "delay": round(node.delay, 2), "balance": simulator.blockchain.get_balance(node.name)}
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
        
        os.makedirs("logs", exist_ok=True)
        with open("logs/transaction_log.csv", mode="a", newline="") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["TX ID", "Sender", "Receiver", "Amount", "Timestamp"])
            writer.writerow([tx.id, sender, receiver, amount, time.time()])
        
        message = "Transaction broadcasted successfully."

    recent_blocks = simulator.blockchain.chain[1:] if len(simulator.blockchain.chain) > 1 else []
    return render_template("transaction.html", message=message, blocks=recent_blocks, nodes=node_names)

@app.route('/mine')
def mine():
    block = simulator.blockchain.mine_block()
    if block:
        simulator.broadcast_block(block)
        return f"Block {block.index} mined with hash: {block.hash}"
    return "No transactions to mine."

@app.route('/attack', methods=["GET", "POST"])
def attack():
    result = None
    if request.method == "POST":
        attacker_node = request.form["attacker_node"]
        victim_node = request.form["victim_node"]
        amount = float(request.form["amount"])
        hash_rate = float(request.form["attacker_hash_rate"])
        delay = float(request.form["network_delay"])
        attacker = AttackerNode(simulator.blockchain, total_honest_hash, attacker_node, victim_node, amount, hash_rate, delay)
        success, reason = attacker.launch_attack()
        result = f"Success: {success} | Reason: {reason}"
    return render_template("attack.html", result=result, nodes=node_names)

@app.route('/stats')
def stats():
    if not os.path.exists("logs/attack_log.csv"):
        return render_template("stats.html", stats=None, plot_url=None)
    df = pd.read_csv("logs/attack_log.csv")
    stats_data = df.to_dict(orient="records")
    
    # Data Visualization
    plot_url = None
    if len(df) > 0:
        # Success rate pie
        success_counts = df['Success'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(success_counts, labels=['Failed', 'Succeeded'], autopct='%1.1f%%', colors=['#e74c3c', '#2ecc71'])
        ax.set_title('Attack Success Rate')
        
        # Hash rate vs success scatter
        df['Success_num'] = df['Success'].astype(int)
        fig2, ax2 = plt.subplots()
        ax2.scatter(df['Hash Rate'], df['Network Delay'], c=df['Success_num'], cmap='RdYlGn', alpha=0.7)
        ax2.set_xlabel('Hash Rate')
        ax2.set_ylabel('Network Delay')
        ax2.set_title('Attack Outcomes by Hash Rate and Delay')
        
        # Combine plots or send one, here base64 for success pie
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plot_url = base64.b64encode(buf.read()).decode('utf-8')
        
    return render_template("stats.html", stats=stats_data, plot_url=plot_url)

@app.route('/tx_logs')
def tx_logs():
    if not os.path.exists("logs/transaction_log.csv"):
        return render_template("stats.html", stats=None)
    df = pd.read_csv("logs/transaction_log.csv")
    return render_template("stats.html", stats=df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)