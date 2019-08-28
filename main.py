import time
import os

from udp_server import UDPServer
from tcp_server import TCPServer
from utils import open_write_pipe, open_read_pipe

TUN2SOCKS_READ_FIFO = "/tmp/tun2socks_read"
TUN2SOCKS_WRITE_FIFO = "/tmp/tun2socks_write"

if __name__ == "__main__":
    write_fd = open_write_pipe(TUN2SOCKS_READ_FIFO)
    read_fd = open_read_pipe(TUN2SOCKS_WRITE_FIFO)

    udpserver = UDPServer(6666, write_fd, read_fd)
    udpserver.run()
    tcpserver = TCPServer(7777, write_fd, read_fd)
    tcpserver.run()

    while True:
        time.sleep(1)

    os.close(write_fd)
    os.close(read_fd)
