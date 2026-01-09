import socket
def test():
    try:
        s = socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("Connected to 8.8.8.8")
        s.close()
    except Exception as e:
        print(f"Failed to connect to 8.8.8.8: {e}")
test()
