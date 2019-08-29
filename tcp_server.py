import os
import threading
import socket
import time

from udpgw import UDPGW
from utils import get_ip_type

class TCPServer:
    def __init__(self, port, write_fd, read_fd):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', port))
        self.sock.listen()
        self.client_map = {}
        self.write_fd = write_fd
        self.read_fd = read_fd
        self.udp_gateway = UDPGW(self.handle_udp_recv)

    def destroy(self):
        self.running = False
        self.udp_gateway.destroy()

    def run(self):
        self.running = True
        self.accept_thread = threading.Thread(target=self.handle_accept)
        self.accept_thread.start()
        self.fifo_read_thread = threading.Thread(target=self.handle_fifo_read)
        self.fifo_read_thread.start()
        self.udp_gateway.run()

    def send_to_client(self, client, data):
        try:
            # decide which client to send
            client.sendall(self.wrap_data(data))
            print("send to client len: " + str(len(data)))
        except Exception:
            client.close()

    def handle_accept(self):
        while self.running:
            client, _ = self.sock.accept()
            client_thread = threading.Thread(target=self.handle_client_recv, args=(client,))
            client_thread.start()

    def handle_fifo_read(self):
        while self.running:
            data = os.read(self.read_fd, 3000)
            while len(data) != 0:
                send_data = None
                # length
                if data[0] & 0xf0 == 0x40:
                    # ipv4
                    # get length
                    total_length = 256 * data[2] + data[3]
                    # ready to handle
                    send_data = data[:total_length]
                    data = data[total_length:]
                elif data[0] & 0xf0 == 0x60:
                    # todo: ipv6
                    # get length
                    payload_length = 256 * data[4] + data[5]
                    total_length = payload_length + 40
                    # ready to handle
                    send_data = data[:total_length]
                    data = data[total_length:]
                else:
                    # unknown packet
                    break

                if not send_data:
                    continue

                send_data = b'\x02' + send_data
                print("read from pipe len: " + str(len(send_data)))
                # todo
                self.send_to_client(self.client_map[b'\x0a\x00\x00\x04'], send_data)

    def handle_client_recv(self, client):
        recv_buf = b''
        while self.running:
            try:
                data = client.recv(3000)
                recv_buf += data
            except Exception:
                client.close()
                break

            if len(recv_buf) < 2:
                time.sleep(0.001)
                continue

            length = recv_buf[0] * 256 + recv_buf[1]
            if len(recv_buf) < 2 + length:
                time.sleep(0.001)
                continue

            data = recv_buf[2:2 + length]
            recv_buf = recv_buf[2 + length:]

            print("recv from client len: " + str(len(data)))

            cmd = data[0]
            if cmd == 0x01:
                # handshake
                send_data = b'\x01'
                send_data += b'\x0a\x00\x00\x04'  # todo: hardcoded
                self.client_map[b'\x0a\x00\x00\x04'] = client
                try:
                    client.sendall(self.wrap_data(send_data))
                except Exception:
                    client.close()
                    break
            elif cmd == 0x02:
                data = data[1:]
                ip_type = get_ip_type(data)
                if ip_type == 4:
                    protocol = data[9]
                    if protocol == 0x06:  # TCP
                        print("write to pipe len: " + str(len(data)))
                        os.write(self.write_fd, data)
                    elif protocol == 0x11:  # UDP
                        self.udp_gateway.recv_local(data)
                elif ip_type == 6:
                    pass  # todo: ipv6

    def handle_udp_recv(self, data):
        self.send_to_client(self.client_map[b'\x0a\x00\x00\x04'], b'\x02' + data)

    def wrap_data(self, data):
        length = len(data)
        return bytes([length >> 8, length % 256]) + data
