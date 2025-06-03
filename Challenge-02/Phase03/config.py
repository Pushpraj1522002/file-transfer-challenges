SERVER_HOST = "localhost"
SERVER_PORT = 9999
CHUNK_SIZE = 1024
PACKET_DROP_RATE = 0.1  # 10% chance of packet drop
PACKET_CORRUPT_RATE = 0.05  # 5% chance of packet corruption
ACK_TIMEOUT = 2.0  # Timeout in seconds for waiting for ACK/NACK
MAX_RETRIES = 3  # Maximum number of retransmission attempts 