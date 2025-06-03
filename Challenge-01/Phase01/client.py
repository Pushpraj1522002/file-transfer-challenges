import socket
import os

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001
BUFFER_SIZE = 4096

filename = "sample_file.txt"
filesize = os.path.getsize(filename)

client_socket = socket.socket()
client_socket.connect((SERVER_HOST, SERVER_PORT))
client_socket.send(filename.encode())

with open(filename, "rb") as f:
    while True:
        bytes_read = f.read(BUFFER_SIZE)
        if not bytes_read:
            break
        client_socket.sendall(bytes_read)

client_socket.close()
