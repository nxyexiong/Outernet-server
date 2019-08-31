import time

from server import Server


if __name__ == "__main__":
    print("start Outernet server")

    server = Server(b'nxyexiong', 6666, 'tun0')
    server.run()

    while True:
        time.sleep(1)
