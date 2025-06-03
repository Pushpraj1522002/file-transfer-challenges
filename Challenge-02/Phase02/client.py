import socket
import sys
from config import SERVER_HOST, SERVER_PORT, CHUNK_SIZE
from utils import calculate_checksum

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_HOST, SERVER_PORT))

    file_path = sys.argv[1] if len(sys.argv) > 1 else "test_files/client1.txt"
    with open(file_path, "rb") as f:
        data = f.read()
        for i in range(0, len(data), CHUNK_SIZE):
            client.sendall(data[i:i+CHUNK_SIZE])

    client.shutdown(socket.SHUT_WR)

    # Receive checksum
    checksum = client.recv(64).decode()
    print(f"[+] Received Checksum: {checksum}")

    # Receive data with headers
    received_chunks = {}
    while True:
        header = client.recv(13)  # Format: "CLIENTID:SEQ|"
        if not header:
            break
        header_decoded = header.decode(errors='ignore').strip()  # decode safely
        print(f"[DEBUG] Raw header received: '{header_decoded}'")

        if ":" not in header_decoded or "|" not in header_decoded:
            print(f"[ERROR] Malformed header: '{header_decoded}'")
            continue  # skip or handle error

        try:
            client_id_part, seq_part = header_decoded.split(":")
            seq_num = int(seq_part.split("|")[0])
        except Exception as e:
            print(f"[ERROR] Failed to parse header: {e}")
            continue

        chunk = client.recv(CHUNK_SIZE)
        if not chunk:
            print("[ERROR] Missing chunk after header.")
            break

        received_chunks[seq_num] = chunk

    # Reassemble in order
    received_data = b''.join(received_chunks[i] for i in sorted(received_chunks))

    new_checksum = calculate_checksum(received_data)
    print("[+] File verification:", "Successful" if new_checksum == checksum else "Failed")

    client.close()

if __name__ == "__main__":
    main()
