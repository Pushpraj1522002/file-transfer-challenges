import socket
import threading
import time
from config import SERVER_HOST, SERVER_PORT, CHUNK_SIZE, ACK_TIMEOUT, MAX_RETRIES
from utils import calculate_checksum, simulate_packet_drop, corrupt_packet, create_packet_header, parse_packet_header

def send_packet_with_retry(conn, client_id, seq_num, data):
    """Send a packet with retransmission logic"""
    retries = 0
    while retries < MAX_RETRIES:
        # Simulate packet drop
        if simulate_packet_drop():
            print(f"[!] Simulated packet drop for seq {seq_num}")
            time.sleep(ACK_TIMEOUT)
            retries += 1
            continue

        # Create and send packet
        header = create_packet_header(client_id, seq_num)
        packet = corrupt_packet(data)  # Simulate corruption
        try:
            print(f"[+] Sending packet {seq_num}")
            conn.sendall(header)
            conn.sendall(packet)

            # Wait for ACK/NACK
            conn.settimeout(ACK_TIMEOUT)
            response = conn.recv(20)  # Receive header
            if not response:
                raise socket.timeout("No response received")

            _, resp_seq, status = parse_packet_header(response)
            if status == "ACK" and resp_seq == seq_num:
                print(f"[+] Packet {seq_num} acknowledged")
                return True
            elif status == "NACK" and resp_seq == seq_num:
                print(f"[!] Packet {seq_num} corrupted, retrying...")
                retries += 1
            else:
                print(f"[!] Invalid response for packet {seq_num}")
                retries += 1

        except (socket.timeout, ConnectionResetError, BrokenPipeError) as e:
            print(f"[!] Error during packet {seq_num} transmission: {e}")
            retries += 1
            if retries >= MAX_RETRIES:
                break
            time.sleep(ACK_TIMEOUT)

    print(f"[!] Max retries exceeded for packet {seq_num}")
    return False

def send_checksum(conn, checksum, client_id):
    """Send checksum with retry logic"""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            print(f"[+] Sending checksum to client {client_id}")
            # Send a special header first
            header = create_packet_header(client_id, -2, is_ack=True)  # -2 indicates checksum
            conn.sendall(header)
            time.sleep(0.1)  # Small delay
            # Send the checksum
            conn.sendall(checksum.encode())
            return True
        except Exception as e:
            print(f"[!] Error sending checksum: {e}")
            retries += 1
            if retries >= MAX_RETRIES:
                return False
            time.sleep(ACK_TIMEOUT)
    return False

def handle_client(conn, addr, client_id):
    print(f"[+] Client {client_id} connected from {addr}")
    file_data = b""
    
    try:
        conn.settimeout(ACK_TIMEOUT)
        # Receive file data
        print(f"[+] Waiting for file data from client {client_id}")
        while True:
            try:
                chunk = conn.recv(CHUNK_SIZE)
                if not chunk:
                    break
                file_data += chunk
                print(f"[+] Received {len(chunk)} bytes")
            except socket.timeout:
                print(f"[!] Timeout waiting for data from client {client_id}")
                break
            except (ConnectionResetError, BrokenPipeError):
                print(f"[!] Connection lost while receiving data from client {client_id}")
                return

        if not file_data:
            print(f"[!] No data received from client {client_id}")
            return

        print(f"[+] Received total of {len(file_data)} bytes")
        checksum = calculate_checksum(file_data)
        
        # Send checksum with retry logic
        if not send_checksum(conn, checksum, client_id):
            print(f"[!] Failed to send checksum to client {client_id}")
            return

        # Send file back with sequence numbers and error simulation
        total_chunks = (len(file_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
        print(f"[+] Sending {total_chunks} chunks back to client {client_id}")
        
        # Reset timeout for sending data
        conn.settimeout(None)  # No timeout for sending
        
        for seq_num in range(total_chunks):
            chunk = file_data[seq_num * CHUNK_SIZE:(seq_num + 1) * CHUNK_SIZE]
            if not send_packet_with_retry(conn, client_id, seq_num, chunk):
                print(f"[!] Failed to send packet {seq_num} after {MAX_RETRIES} retries")
                break
            time.sleep(0.01)  # Small delay between packets

        # Send end of transmission marker
        try:
            end_header = create_packet_header(client_id, -1)  # Special sequence number for end
            conn.sendall(end_header)
        except:
            pass

    except Exception as e:
        print(f"[!] Error handling client {client_id}: {e}")
    finally:
        try:
            conn.close()
        except:
            pass
        print(f"[-] Client {client_id} disconnected")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    print(f"[*] Server listening on {SERVER_HOST}:{SERVER_PORT}")
    
    client_id = 0
    while True:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr, client_id))
            thread.start()
            client_id += 1
        except KeyboardInterrupt:
            print("\n[!] Server shutting down...")
            break
        except Exception as e:
            print(f"[!] Error accepting connection: {e}")

if __name__ == "__main__":
    main() 