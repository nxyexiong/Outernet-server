import os
import threading
import socket
import time

from udpgw import UDPGW
from utils import get_ip_type

class UDPServer:
    def __init__(self, port, write_fd, read_fd):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        self.client_map = {}
        self.write_fd = write_fd
        self.read_fd = read_fd
        self.udp_gateway = UDPGW(self.handle_udp_recv)

    def destroy(self):
        self.running = False
        self.udp_gateway.destroy()

    def run(self):
        self.running = True
        self.client_recv_thread = threading.Thread(target=self.handle_client_recv)
        self.client_recv_thread.start()
        self.fifo_read_thread = threading.Thread(target=self.handle_fifo_read)
        self.fifo_read_thread.start()
        self.udp_gateway.run()

    def send_to_client(self, client_addr, data):
        # decide which client to send
        self.sock.sendto(data, client_addr)

    def handle_fifo_read(self):
        data = b''
        while self.running:
            tmp = os.read(self.read_fd, 1500)
            data += tmp
            while len(data) > 0:
                send_data = None
                # length
                if data[0] & 0xf0 == 0x40:
                    # ipv4
                    # get length
                    if 4 > len(data):
                        break
                    total_length = 256 * data[2] + data[3]
                    # ready to handle
                    if total_length > len(data):
                        break
                    send_data = data[:total_length]
                    data = data[total_length:]
                elif data[0] & 0xf0 == 0x60:
                    # todo: ipv6
                    # get length
                    if 6 > len(data):
                        break
                    payload_length = 256 * data[4] + data[5]
                    total_length = payload_length + 40
                    # ready to handle
                    if total_length > len(data):
                        break
                    send_data = data[:total_length]
                    data = data[total_length:]
                else:
                    # unknown packet
                    data = b''
                    break

                if not send_data:
                    continue

                #print("read from pipe len: " + str(len(send_data)))
                # todo
                send_data = b'\x02' + send_data
                self.send_to_client(self.client_map[b'\x0a\x00\x00\x04'], send_data)

    def handle_client_recv(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(2000)
            except Exception:
                continue

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
                    protocol = data[9]
                    if protocol == 0x06:  # TCP
                        #print("write to pipe len: " + str(len(data)))
                        os.write(self.write_fd, data)
                    elif protocol == 0x11:  # UDP
                        self.udp_gateway.recv_local(data)
                elif ip_type == 6:
                    pass  # todo: ipv6

    def handle_udp_recv(self, data):
        self.send_to_client(self.client_map[b'\x0a\x00\x00\x04'], b'\x02' + data)
