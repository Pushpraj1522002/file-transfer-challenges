import socket
import os
import hashlib

CHUNK_SIZE = 1024
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5001

def compute_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def send_chunks(client_socket, file_path):
    checksum = compute_checksum(file_path)
    client_socket.send(checksum.encode())  # send checksum

    with open(file_path, 'rb') as f:
        seq = 0
        while chunk := f.read(CHUNK_SIZE):
            header = f"{seq:08d}".encode()  # fixed 8-byte sequence header
            client_socket.send(header + chunk)
            seq += 1

    client_socket.send(b"END")  # signal end of transfer

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
