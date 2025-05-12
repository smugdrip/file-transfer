import socket
import tarfile
import os
import sys
import key
import cryptography as c
import struct

# get ip to send to
host = input('enter receiver IP address (10.1.0.145): ')
if not host:
    host = '10.1.0.145'
port = 5001

print('trying to send to: ', host, port)

directory = input('enter directory to send (./send-files): ')
if not directory:
    directory = './send-files'

if not os.path.isdir(directory):
    print(f"Error: '{directory}' is not a valid directory.")
    sys.exit(1)

# Compress into .tar
tar_path =  'send-archive.tar'
with tarfile.open(tar_path, 'w') as tar:
    tar.add(directory, arcname=os.path.basename(directory), recursive=True)

# Encryption set-up
pswd = str(input('Enter password to encrypt with: '))
salt = os.urandom(16)
fernet_key = key.get_fernet_key(pswd, salt)
fernet = c.Fernet(fernet_key)

# Send the tar file
count = 0
with socket.socket() as s:
    s.connect((host, port))
    # send the salt first
    s.sendall(salt)
    with open(tar_path, 'rb') as f:
        while (chunk := f.read(4096)):
            print(count, end=' ')
            s.sendall(fernet.encrypt(chunk))

os.remove(tar_path)
print("Directory sent successfully.")
