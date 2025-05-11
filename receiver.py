import socket
import tarfile
import os

host = '0.0.0.0'
port = 5001
output_dir = 'received-files'

os.makedirs(output_dir, exist_ok=True)

with socket.socket() as s:
    s.bind((host, port))
    s.listen(1)
    print(f"Listening on {host}:{port}...")
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        archive_path = os.path.join(output_dir, 'received.tar')
        with open(archive_path, 'wb') as f:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                f.write(data)

# Extract the tar file
with tarfile.open(archive_path, 'r') as tar:
    tar.extractall(path=output_dir)

print(f"Files received and extracted to '{output_dir}/'")
