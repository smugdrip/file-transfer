import socket
import tarfile
import os
import sys

host = input('Enter receiver IP address (10.1.0.145): ')
port = 5001

if len(sys.argv) != 2:
    print("Usage: python3 sender.py <directory_to_send>")
    sys.exit(1)

directory = sys.argv[1]

if not os.path.isdir(directory):
    print(f"Error: '{directory}' is not a valid directory.")
    sys.exit(1)

# Archive the directory into a .tar file
tar_path = 'send_temp.tar'
with tarfile.open(tar_path, 'w') as tar:
    tar.add(directory, arcname=os.path.basename(directory))

# Send the tar file
with socket.socket() as s:
    s.connect((host, port))
    with open(tar_path, 'rb') as f:
        while (chunk := f.read(4096)):
            s.sendall(chunk)

os.remove(tar_path)
print("Directory sent successfully.")
