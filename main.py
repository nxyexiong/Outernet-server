import time
import os
import sys

from udp_server import UDPServer
from tcp_server import TCPServer
from utils import open_write_pipe, open_read_pipe

TUN2SOCKS_READ_FIFO = "/tmp/tun2socks_read"
TUN2SOCKS_WRITE_FIFO = "/tmp/tun2socks_write"

enable_udp = False
enable_tcp = False


def parse_args(args):
    global enable_udp
    global enable_tcp

    count = len(args)
    for i in range(count):
        if args[i] == '--udp':
            enable_udp = True
        elif args[i] == '--tcp':
            enable_tcp = True


if __name__ == "__main__":
    parse_args(sys.argv)

    write_fd = open_write_pipe(TUN2SOCKS_READ_FIFO)
    read_fd = open_read_pipe(TUN2SOCKS_WRITE_FIFO)

    if enable_udp:
        udpserver = UDPServer(6666, write_fd, read_fd)
        udpserver.run()

    if enable_tcp:
        tcpserver = TCPServer(7777, write_fd, read_fd)
        tcpserver.run()

    while True:
        time.sleep(1)

    os.close(write_fd)
    os.close(read_fd)
