import socket
from config import SERVER_HOST, SERVER_PORT, CHUNK_SIZE
from utils import calculate_checksum

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_HOST, SERVER_PORT))

    with open("test_files/sample.txt", "rb") as f:
        data = f.read()
        for i in range(0, len(data), CHUNK_SIZE):
            client.sendall(data[i:i+CHUNK_SIZE])

    client.shutdown(socket.SHUT_WR)

    # Receive checksum
    checksum = client.recv(64).decode()
    print(f"[+] Received Checksum: {checksum}")

    # Receive file back
    received_data = b""
    while True:
        chunk = client.recv(CHUNK_SIZE)
        if not chunk:
            break
        received_data += chunk

    new_checksum = calculate_checksum(received_data)
    print("[+] File verification:", "Successful" if new_checksum == checksum else "Failed")

    client.close()

if __name__ == "__main__":
    main()
