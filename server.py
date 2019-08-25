import os
import threading
import socket
import time

from utils import open_read_pipe, open_write_pipe, get_ip_type

TUN2SOCKS_READ_FIFO = "/tmp/tun2socks_read"
TUN2SOCKS_WRITE_FIFO = "/tmp/tun2socks_write"

class Server:
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        self.client_map = {}
        self.write_fd = open_write_pipe(TUN2SOCKS_READ_FIFO)
        self.read_fd = open_read_pipe(TUN2SOCKS_WRITE_FIFO)

    def destroy(self):
        os.close(self.write_fd)
        os.close(self.read_fd)

    def run(self):
        self.client_recv_thread = threading.Thread(target=self.handle_client_recv)
        self.client_recv_thread.start()
        self.fifo_read_thread = threading.Thread(target=self.handle_fifo_read)
        self.fifo_read_thread.start()

    def send_to_client(self, client_addr, data):
        # decide which client to send
        self.sock.sendto(data, client_addr)

    def handle_fifo_read(self):
        while True:
            data = os.read(self.read_fd, 65536)
            data = b'\x02' + data
            print("read from pipe len: " + str(len(data)))
            # todo
            self.send_to_client(self.client_map[b'\x0a\x00\x00\x04'], data)

    def handle_client_recv(self):
        while True:
            data, addr = self.sock.recvfrom(65536)

            print("recv a packet len: " + str(len(data)))

            cmd = data[0]
            if cmd == 0x01:
                # handshake
                send_data = b'\x01'
                send_data += b'\x0a\x00\x00\x04'  # todo: hardcoded
                self.client_map[b'\x0a\x00\x00\x04'] = addr
                self.send_to_client(addr, send_data)
            elif cmd == 0x02:
                data = data[1:]
                ip_type = get_ip_type(data)
                if ip_type == 4:
                    print("write to pipe: " + str(data))
                    os.write(self.write_fd, data)
                elif ip_type == 6:
                    pass  # todo: ipv6
