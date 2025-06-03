import hashlib

def calculate_checksum(file_data):
    return hashlib.sha256(file_data).hexdigest()
