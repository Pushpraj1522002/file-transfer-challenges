import hashlib
import random
import time
from config import PACKET_DROP_RATE, PACKET_CORRUPT_RATE

def calculate_checksum(data):
    return hashlib.sha256(data).hexdigest()

def simulate_packet_drop():
    """Simulate packet drop based on configured probability"""
    return random.random() < PACKET_DROP_RATE

def corrupt_packet(data):
    """Simulate packet corruption by randomly flipping bits"""
    if random.random() < PACKET_CORRUPT_RATE:
        # Convert to bytearray for modification
        data_array = bytearray(data)
        # Flip a random bit in a random position
        pos = random.randint(0, len(data_array) - 1)
        data_array[pos] ^= 0xFF
        return bytes(data_array)
    return data

def create_packet_header(client_id, seq_num, is_ack=False, is_nack=False):
    """Create a packet header with status flags"""
    status = "ACK" if is_ack else "NACK" if is_nack else "DATA"
    header = f"{client_id}:{seq_num:06d}:{status}|"
    # Pad header to 20 bytes
    header = header.ljust(20)
    return header.encode('ascii')

def parse_packet_header(header):
    """Parse packet header and return components"""
    try:
        header_str = header.decode('ascii').strip()
        client_id, seq_num, status = header_str.split(':')
        return int(client_id), int(seq_num), status
    except Exception as e:
        raise ValueError(f"Invalid header format: {e}") 