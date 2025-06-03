import socket
import os
from config import SERVER_HOST, SERVER_PORT, CHUNK_SIZE
from utils import calculate_checksum

def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")
    file_data = b""
    
    while True:
        chunk = conn.recv(CHUNK_SIZE)
        if not chunk:
            break
        file_data += chunk

    checksum = calculate_checksum(file_data)
    print(f"[+] Checksum: {checksum}")
    conn.sendall(checksum.encode())

    # Send back file
    for i in range(0, len(file_data), CHUNK_SIZE):
        conn.sendall(file_data[i:i+CHUNK_SIZE])

    conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    print(f"[*] Server listening on {SERVER_HOST}:{SERVER_PORT}")
    
    conn, addr = server.accept()
    handle_client(conn, addr)

if __name__ == "__main__":
    main()
