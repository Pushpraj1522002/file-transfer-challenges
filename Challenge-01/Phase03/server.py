import socket
import os
import hashlib
import random

CHUNK_SIZE = 1024
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5001

def compute_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def prepare_chunks(file_path):
    chunks = []
    with open(file_path, 'rb') as f:
        seq = 0
        while chunk := f.read(CHUNK_SIZE):
            chunk_len = len(chunk)
            header = f"{seq:08d}{chunk_len:04d}".encode()  # 12 bytes: 8 for seq, 4 for size
            chunks.append((seq, header + chunk))
            seq += 1
    return chunks

def send_chunks(client_socket, file_path):
    checksum = compute_checksum(file_path)
    client_socket.send(checksum.encode())  # Step 1: send checksum

    chunks = prepare_chunks(file_path)
    random.shuffle(chunks)  # Optional: simulate out-of-order delivery

    for _, data in chunks:
        client_socket.send(data)

    # Send termination header: sequence = -1 → "-0000001" and dummy size "0000"
    client_socket.send(f"-00000010000".encode())  # 12-byte end signal

# --- Main server setup ---
server_socket = socket.socket()
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

client_socket, address = server_socket.accept()
print(f"[+] {address} is connected.")

filename = client_socket.recv(1024).decode()
send_chunks(client_socket, filename)

client_socket.close()
server_socket.close()
