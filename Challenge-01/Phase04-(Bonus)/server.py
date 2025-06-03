import socket
import os
import hashlib
import random
import struct

CHUNK_SIZE = 1024
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5001
CORRUPTION_PROBABILITY = 0.2  # 20% chance to corrupt a chunk

def compute_checksum(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def prepare_chunks(file_path):
    chunks = []
    with open(file_path, 'rb') as f:
        seq = 0
        while chunk := f.read(CHUNK_SIZE):
            checksum = compute_checksum(chunk)
            header = f"{seq:08d}".encode()
            chunks.append((seq, header, checksum.encode(), chunk))
            seq += 1
    return chunks

def corrupt_data(data):
    data = bytearray(data)
    index = random.randint(0, len(data) - 1)
    data[index] ^= 0xFF  # Flip one byte
    return bytes(data)

# --- Main server setup ---
server_socket = socket.socket()
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

client_socket, address = server_socket.accept()
print(f"[+] {address} is connected.")

filename = client_socket.recv(1024).decode()
print(f"[Server] Requested file: {filename}")

chunks = prepare_chunks(filename)

# Send number of chunks first
client_socket.send(f"{len(chunks):08d}".encode())

for seq, header, checksum, chunk in chunks:
    while True:
        corrupted_chunk = corrupt_data(chunk) if random.random() < CORRUPTION_PROBABILITY else chunk
        chunk_length_bytes = struct.pack('!I', len(corrupted_chunk))  # 4-byte length

        # Send header + checksum + chunk_length + chunk
        client_socket.sendall(header + checksum + chunk_length_bytes + corrupted_chunk)

        # Wait for ACK/NACK
        ack = client_socket.recv(4).decode()
        if ack == "ACK":
            break
        elif ack == "NACK":
            print(f"[Server] Chunk {seq} corrupted. Resending...")
        else:
            print("[Server] Invalid response. Terminating.")
            break

# Tell client transfer is done
client_socket.send(f"{-1:08d}".encode())

client_socket.close()
server_socket.close()
