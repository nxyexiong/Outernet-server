import time

from server import Server

if __name__ == "__main__":
    server = Server(6666)
    server.run()

    while True:
        time.sleep(1)
