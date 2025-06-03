import socket
import hashlib

CHUNK_SIZE = 1024
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001

client_socket = socket.socket()
client_socket.connect((SERVER_HOST, SERVER_PORT))

filename = "sample_file.txt"
client_socket.send(filename.encode())

received_chunks = {}

# Step 1: Receive checksum
checksum = client_socket.recv(64).decode()
print(f"[Client] Checksum received: {checksum}")

# Step 2: Receive chunks
while True:
    header = client_socket.recv(8)
    if header == b"END":
        break
    seq = int(header.decode())
    chunk = client_socket.recv(CHUNK_SIZE)
    received_chunks[seq] = chunk

# Step 3: Reassemble in order
reconstructed = b''.join([received_chunks[i] for i in sorted(received_chunks)])

# Step 4: Save to file
with open("reconstructed_" + filename, "wb") as f:
    f.write(reconstructed)

# Step 5: Verify checksum
sha256 = hashlib.sha256()
sha256.update(reconstructed)
recomputed = sha256.hexdigest()

if recomputed == checksum:
    print("[Client] Transfer successful. Checksum verified.")
else:
    print("[Client] Checksum mismatch! Transfer failed.")

client_socket.close()
