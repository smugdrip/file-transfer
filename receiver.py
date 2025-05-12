import socket
import tarfile
import os
import time
import key
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
import sys

host = '0.0.0.0'
port = 5001
output_dir = input('Enter directory name to store received files: ')
alpha = 0.2

os.makedirs(output_dir, exist_ok=True)

total_received_bytes = 0
ewma_kbps = 0.0
stat_report_interval_seconds = 1.0
last_stat_report_time = time.time()
total_bytes_at_last_report = 0
first_ewma_value_set = False
salt = bytes()
encrypted_archive_path = os.path.join(output_dir, 'received.encrypted')
decrypted_archive_path = os.path.join(output_dir, 'received.tar')

pswd = str(input('Enter password to decrypt with: '))
if not pswd:
    sys.exit()

with socket.socket() as s:
    s.bind((host, port))
    s.listen(1)
    print(f"Listening on {host}:{port}...")
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        archive_path = os.path.join(output_dir, 'received.tar')
        # get the salt first
        salt = conn.recv(16)
        print(f"Received salt: {salt.hex()}")
        with open(archive_path, 'wb') as f:
            start_time = time.time()
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                f.write(data)
                total_received_bytes += len(data)

                current_time = time.time()
                elapsed_since_last_report = current_time - last_stat_report_time

                if elapsed_since_last_report >= stat_report_interval_seconds:
                    bytes_this_period = total_received_bytes - total_bytes_at_last_report
                    
                    if elapsed_since_last_report > 0:
                        kbps = (bytes_this_period * 8) / (elapsed_since_last_report * 1000)
                    else:
                        kbps = 0

                    if not first_ewma_value_set:
                        ewma_kbps = kbps
                        first_ewma_value_set = True
                    else:
                        ewma_kbps = alpha * kbps + (1 - alpha) * ewma_kbps

                    print(f"Timestamp: {(current_time - start_time):.2f}s, Total Bytes: {total_received_bytes}, EWMA: {ewma_kbps:.2f} Kbps")
                    
                    last_stat_report_time = current_time
                    total_bytes_at_last_report = total_received_bytes

print(f"\nTotal {total_received_bytes} bytes received.")
print(f"Final EWMA Transfer Rate: {ewma_kbps:.2f} Kbps.")

# decrypt and extract
if total_received_bytes > 0 and os.path.exists(archive_path):

    try:
        fernet_key = key.get_fernet_key(pswd, salt)
        fernet = Fernet(fernet_key)
        chunk_size = 32000

        with open(encrypted_archive_path, 'rb') as encrypted_file:
            with open(decrypted_archive_path, 'wb') as decrypted_file:
                while True:
                    chunk = encrypted_file.read(chunk_size)
                    if not chunk:
                        break
                    try:
                        decrypted_chunk = fernet.decrypt(chunk)
                        decrypted_file.write(decrypted_chunk)
                    except InvalidToken:
                        print("\nDecryption failed: Invalid password or corrupted data in a chunk.")
                        os.remove(decrypted_archive_path)
                        break 

        print(f"\nSuccessfully decrypted the received file to '{decrypted_archive_path}'")

        # extract the .tar file
        try:
            with tarfile.open(decrypted_archive_path, 'r') as tar:
                tar.extractall(path=output_dir)
            print(f"Files extracted to '{output_dir}/'")
        except tarfile.ReadError as e:
            print(f"\nError extracting tar file: {e}. It might be corrupted or not a valid tar archive after decryption.")
        except FileNotFoundError:
            print(f"\nDecrypted archive file {decrypted_archive_path} not found for extraction.")
    except InvalidToken:
        print("\nDecryption failed: Invalid password or corrupted data.")
    except Exception as e:
        print(f"\nAn error occurred during decryption: {e}")
else:
    if total_received_bytes == 0:
        print("\nNo data received.")
    else: # os.path.exists(archive_path) is false, but total_received_bytes > 0 (highly unlikely)
        print(f"\nArchive file {archive_path} was not created despite receiving data.")


print(f"\nTotal {total_received_bytes} bytes received.")
print(f"Final EWMA Transfer Rate: {ewma_kbps:.2f} Kbps.")

print()
