import socket
import threading
from config import SERVER_HOST, SERVER_PORT, CHUNK_SIZE
from utils import calculate_checksum

def handle_client(conn, addr, client_id):
    print(f"[+] Client {client_id} connected from {addr}")
    file_data = b""
    
    while True:
        chunk = conn.recv(CHUNK_SIZE)
        if not chunk:
            break
        file_data += chunk

    checksum = calculate_checksum(file_data)
    conn.sendall(checksum.encode())

    # Send file back with sequence numbers and client ID
    for seq_num in range(0, len(file_data), CHUNK_SIZE):
        chunk = file_data[seq_num:seq_num + CHUNK_SIZE]
        header_str = f"{client_id}:{seq_num // CHUNK_SIZE:06d}|"
        header_bytes = header_str.encode("ascii")
        # Pad header to 13 bytes
        if len(header_bytes) < 13:
            header_bytes += b' ' * (13 - len(header_bytes))
        elif len(header_bytes) > 13:
            raise ValueError(f"Header too long: {header_bytes}")
        conn.sendall(header_bytes)
        conn.sendall(chunk)

    conn.close()
    print(f"[-] Client {client_id} disconnected")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    print(f"[*] Server listening on {SERVER_HOST}:{SERVER_PORT}")
    
    client_id = 0
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr, client_id))
        thread.start()
        client_id += 1

if __name__ == "__main__":
    main()
