import socket
import time

def test_conn():
    host = "generativelanguage.googleapis.com"
    port = 443
    print(f"Testing connectivity to {host}:{port}...")
    try:
        start = time.time()
        s = socket.create_connection((host, port), timeout=5)
        end = time.time()
        print(f"Connected in {end-start:.2f}s")
        s.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_conn()
