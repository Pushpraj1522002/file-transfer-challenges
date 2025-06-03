import socket
import sys
import time
from config import SERVER_HOST, SERVER_PORT, CHUNK_SIZE, ACK_TIMEOUT
from utils import calculate_checksum, create_packet_header, parse_packet_header

def send_ack_nack(conn, client_id, seq_num, is_ack=True):
    """Send ACK or NACK for a packet"""
    header = create_packet_header(client_id, seq_num, is_ack=is_ack, is_nack=not is_ack)
    conn.sendall(header)

def receive_checksum(conn, client_id):
    """Receive checksum with retry logic"""
    retries = 0
    while retries < 3:  # Try 3 times to receive checksum
        try:
            print("[+] Waiting for checksum...")
            # First receive the header
            header = conn.recv(20)
            if not header:
                raise socket.timeout("No header received")

            _, seq_num, status = parse_packet_header(header)
            if seq_num != -2:  # -2 is our special checksum sequence number
                raise ValueError("Invalid header for checksum")

            # Then receive the checksum
            checksum = conn.recv(64).decode()
            if not checksum:
                raise socket.timeout("No checksum received")

            print(f"[+] Received Checksum: {checksum}")
            return checksum

        except socket.timeout:
            print(f"[!] Timeout waiting for checksum (attempt {retries + 1}/3)")
            retries += 1
            if retries >= 3:
                raise
            time.sleep(0.1)
        except Exception as e:
            print(f"[!] Error receiving checksum: {e}")
            retries += 1
            if retries >= 3:
                raise
            time.sleep(0.1)

def main():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(ACK_TIMEOUT)  # Set default timeout
        client.connect((SERVER_HOST, SERVER_PORT))
        print(f"[+] Connected to server at {SERVER_HOST}:{SERVER_PORT}")

        # Send file to server
        file_path = sys.argv[1] if len(sys.argv) > 1 else "test_files/client1.txt"
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                print(f"[+] Sending file: {file_path} ({len(data)} bytes)")
                for i in range(0, len(data), CHUNK_SIZE):
                    client.sendall(data[i:i+CHUNK_SIZE])
                print("[+] File sent successfully")
        except FileNotFoundError:
            print(f"[!] Error: File {file_path} not found")
            return
        except Exception as e:
            print(f"[!] Error reading file: {e}")
            return

        # Receive checksum
        try:
            checksum = receive_checksum(client, 0)  # client_id is 0 for now
        except Exception as e:
            print(f"[!] Failed to receive checksum: {e}")
            return

        # Reset timeout for receiving data
        client.settimeout(None)  # No timeout for receiving data

        # Receive data with headers and send ACK/NACK
        received_chunks = {}
        expected_seq = 0
        start_time = time.time()
        
        while True:
            try:
                # Receive header
                print(f"[+] Waiting for packet {expected_seq}...")
                header = client.recv(20)
                if not header:
                    print("[+] Server closed connection")
                    break

                client_id, seq_num, status = parse_packet_header(header)
                
                # Check for end of transmission
                if seq_num == -1:
                    print("[+] End of transmission received")
                    break

                print(f"[+] Received header for packet {seq_num}")
                
                # Receive chunk
                chunk = client.recv(CHUNK_SIZE)
                if not chunk:
                    print("[!] Missing chunk after header.")
                    break

                # Verify chunk integrity
                chunk_checksum = calculate_checksum(chunk)
                original_checksum = calculate_checksum(data[seq_num * CHUNK_SIZE:(seq_num + 1) * CHUNK_SIZE])
                
                if chunk_checksum == original_checksum:
                    print(f"[+] Packet {seq_num} received correctly")
                    received_chunks[seq_num] = chunk
                    send_ack_nack(client, client_id, seq_num, is_ack=True)
                else:
                    print(f"[!] Packet {seq_num} corrupted")
                    send_ack_nack(client, client_id, seq_num, is_ack=False)

                # Check if we've received all chunks
                if len(received_chunks) == (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE:
                    print("[+] All packets received")
                    break

            except socket.timeout:
                print(f"[!] Timeout waiting for packet {expected_seq}")
                break
            except ConnectionResetError:
                print("[!] Connection reset by server")
                break
            except Exception as e:
                print(f"[!] Error during transfer: {e}")
                break

        # Reassemble in order
        received_data = b''.join(received_chunks[i] for i in sorted(received_chunks))
        print(f"[+] Reassembled {len(received_data)} bytes")

        new_checksum = calculate_checksum(received_data)
        print("[+] File verification:", "Successful" if new_checksum == checksum else "Failed")

    except ConnectionRefusedError:
        print(f"[!] Could not connect to server at {SERVER_HOST}:{SERVER_PORT}")
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
    finally:
        try:
            client.close()
        except:
            pass
        print("[-] Connection closed")

if __name__ == "__main__":
    main() 