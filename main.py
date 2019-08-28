import time

from udp_server import UDPServer

if __name__ == "__main__":
    server = UDPServer(6666)
    server.run()

    while True:
        time.sleep(1)
