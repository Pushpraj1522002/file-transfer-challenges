import socket
import hashlib
import struct

CHUNK_SIZE = 1024
HEADER_SIZE = 8
CHECKSUM_SIZE = 64
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

# Step 1: Receive number of chunks
chunk_count = int(recv_all(client_socket, HEADER_SIZE).decode())
print(f"[Client] Expecting {chunk_count} chunks")

# Step 2: Receive chunks
while True:
    header = recv_all(client_socket, HEADER_SIZE)
    if not header:
        break
    seq_str = header.decode()
    if seq_str == "-0000001":
        break

    try:
        seq = int(seq_str)
    except ValueError:
        print("[Client] Invalid header. Terminating.")
        break

    checksum = recv_all(client_socket, CHECKSUM_SIZE).decode()
    chunk_length_bytes = recv_all(client_socket, 4)
    chunk_length = struct.unpack('!I', chunk_length_bytes)[0]

    chunk = recv_all(client_socket, chunk_length)
    if chunk is None:
        print(f"[Client] Failed to receive chunk {seq}")
        client_socket.send("NACK".encode())
        continue

    sha256 = hashlib.sha256()
    sha256.update(chunk)
    if sha256.hexdigest() != checksum:
        print(f"[Client] ❌ Corrupted chunk {seq}")
        client_socket.send("NACK".encode())
        continue

    received_chunks[seq] = chunk
    client_socket.send("ACK".encode())

# Step 3: Reassemble
reconstructed = b''.join(received_chunks[i] for i in sorted(received_chunks))

# Step 4: Save
with open("reconstructed_" + filename, "wb") as f:
    f.write(reconstructed)

print("[Client] ✅ File received successfully.")
client_socket.close()
