import json
import os
from typing import List

from block import Block, create_block, create_block_from_dict, create_genesis_block
from network import broadcast_block, broadcast_transaction


def load_chain(fpath: str) -> List[Block]:
    if os.path.exists(fpath):
        with open(fpath) as f:
            data = json.load(f)
            blockchain = []
            for block_data in data:
                block = create_block_from_dict(block_data)
                blockchain.append(block)
            return blockchain

    return [create_genesis_block()]


def save_chain(fpath: str, chain: list[Block]):
    os.makedirs(os.path.dirname(fpath), exist_ok=True) ## adicionado para garantir que a pasta db/ exista 
    blockchain_serializable = []
    for b in chain:
        blockchain_serializable.append(b.as_dict())

    with open(fpath, "w") as f:
        json.dump(blockchain_serializable, f, indent=2)


def valid_chain(chain: List[Block]) -> bool:
    for i in range(1, len(chain)):
        prev = chain[i - 1]
        curr = chain[i]
        if curr.prev_hash != prev.hash:
            return False
    return True


def replace_chain(new_chain: List[Block], blockchain_fpath: str) -> List[Block]:
    print("[i] Attempting to replace chain...")
    current_chain = load_chain(blockchain_fpath)
    if valid_chain(new_chain) and len(new_chain) > len(current_chain):
        print("[✓] Chain replaced with longer valid chain.")
        save_chain(blockchain_fpath, new_chain)
        return new_chain
    print("[x] Received chain is not longer or not valid.")
    return current_chain


def print_chain(blockchain: List[Block]):
    for b in blockchain:
        print(f"Index: {b.index}, Hash: {b.hash[:10]}..., Tx: {len(b.transactions)}")


def mine_block(
    transactions: List,
    blockchain: List[Block],
    node_id: str,
    reward: int,
    difficulty: int,
    blockchain_fpath: str,
    peers_fpath: str,
    port: int,
):
    
    last_block = blockchain[-1]
    prev_hash = last_block.hash
    index = len(blockchain)

    new_block = create_block(
        transactions,
        prev_hash,
        miner=node_id,
        index=index,
        reward=reward,
        difficulty=difficulty,
    )

    if blockchain[-1].hash != last_block.hash:
        print("[!] Stale block mined. Another node was faster. Discarding block.")
        return

    blockchain.append(new_block)
    transactions.clear()  
    save_chain(blockchain_fpath, blockchain)
    broadcast_block(new_block, peers_fpath, port)
    print(f"[✓] Block {new_block.index} mined and broadcasted successfully.")


def make_transaction(sender, recipient, amount, transactions, peers_file, port):
    tx = {"from": sender, "to": recipient, "amount": amount}
    transactions.append(tx)
    broadcast_transaction(tx, peers_file, port)
    print("[+] Transaction added.")


def get_balance(node_id: str, blockchain: List[Block]) -> float:
    balance = 0
    for block in blockchain:
        for tx in block.transactions:
            if tx["to"] == node_id:
                balance += float(tx["amount"])
            if tx["from"] == node_id:
                balance -= float(tx["amount"])
    return balance


def on_valid_block_callback(fpath, chain):
    save_chain(fpath, chain)