import socket

host = "127.0.0.1"
port = 1234

with socket.create_connection((host, port)) as sock:
    sock.settimeout(1.0)  # <-- allows Ctrl+C to work every 1s
    print("[*] Connected")
    with open("output.h264", "wb") as f:
        try:
            while True:
                try:
                    data = sock.recv(4096)
                    if not data:
                        print("[!] Disconnected")
                        break
                    f.write(data)
                    print(" ".join(f"{b:02X}" for b in data[:32]), "...")
                except socket.timeout:
                    continue  # just retry
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user, closing.")
