import socket
import hashlib

CHUNK_SIZE = 1024
HEADER_SIZE = 12  # 8 bytes for seq + 4 bytes for chunk size
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001

def recv_all(sock, num_bytes):
    data = b''
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            return None
        data += packet
    return data

client_socket = socket.socket()
client_socket.connect((SERVER_HOST, SERVER_PORT))

filename = "sample_file.txt"
client_socket.send(filename.encode())

received_chunks = {}

# Step 1: Receive checksum
checksum = client_socket.recv(64).decode()
print(f"[Client] Checksum received: {checksum}")

# Step 2: Receive all chunks
while True:
    header = recv_all(client_socket, HEADER_SIZE)
    if not header:
        break

    try:
        seq_str = header[:8].decode()
        size_str = header[8:].decode()

        if seq_str == "-0000001":
            break

        seq = int(seq_str)
        size = int(size_str)

        chunk = recv_all(client_socket, size)
        if chunk is None:
            print(f"[Client] Failed to receive chunk {seq}.")
            break

        received_chunks[seq] = chunk
    except Exception as e:
        print(f"[Client] Error parsing header or receiving chunk: {e}")
        break

# Step 3: Reassemble in order
reconstructed = b''.join(received_chunks[i] for i in sorted(received_chunks))

# Step 4: Save to file
with open("reconstructed_" + filename, "wb") as f:
    f.write(reconstructed)

# Step 5: Verify checksum
sha256 = hashlib.sha256()
sha256.update(reconstructed)
recomputed = sha256.hexdigest()

if recomputed == checksum:
    print("[Client] ✅ Transfer successful. Checksum verified.")
else:
    print("[Client] ❌ Checksum mismatch! Transfer failed.")

client_socket.close()
