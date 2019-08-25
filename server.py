import os
import asyncio
import threading
import socket
import queue

from utils import open_read_pipe, open_write_pipe, get_ip_type

TUN2SOCKS_READ_FIFO = "/tmp/tun2socks_read"
TUN2SOCKS_WRITE_FIFO = "/tmp/tun2socks_write"

class Server:
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(0)
        self.sock.bind(('0.0.0.0', port))
        self.client_map = {}
        self.write_fd = open_write_pipe(TUN2SOCKS_READ_FIFO)
        self.read_fd = open_read_pipe(TUN2SOCKS_WRITE_FIFO)

    def destroy(self):
        self.write_fd.close()
        self.read_fd.close()

    def run(self):
        self.thread = threading.Thread(target=self.handle_loop)
        self.thread.start()
        self.fifo_read_thread = threading.Thread(target=self.handle_fifo_read)
        self.fifo_read_thread.start()

    def handle_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.handle_recv())
        self.loop.run_forever()

    def send(self, client_addr, data):
        # decide which client to send
        self.sock.sendto(data, client_addr)

    def handle_fifo_read(self):
        while True:
            data = self.read_fd.read()
            print("read from pipe: " + data)
            # todo

    async def handle_recv(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(65536)
            except socket.error as err:
                # WOULDBLOCK, AGAIN
                if err.errno == 10035 or err.errno == 10036:
                    await asyncio.sleep(0.001)
                    continue
                else:
                    raise err

            print("recv a packet len: " + len(data))

            cmd = data[0]
            if cmd == 0x01:
                # handshake
                send_data = b'\x01'
                send_data += b'\x0a\x00\x00\x04'  # todo: hardcoded
                self.client_map[b'\x0a\x00\x00\x04', addr]
                self.send(addr, send_data)
            elif cmd == 0x02:
                data = data[1:]
                ip_type = get_ip_type(data)
                if ip_type == 4:
                    self.write_fd.write(data)
                elif ip_type == 6:
                    pass  # todo: ipv6
