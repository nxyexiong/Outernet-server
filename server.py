import os
import threading
import socket
import time

from cipher import AESCipher
from tun import TUN

class Server:
    def __init__(self, secret, port, tun_name):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        self.tun = TUN(tun_name, self.handle_tun_read)
        self.cipher = AESCipher(secret)
        self.client_addr = None

    def run(self):
        self.tun.run()
        self.recv_thread = threading.Thread(target=self.handle_recv)
        self.recv_thread.start()

    def send_to_client(self, data):
        if not self.client_addr:
            return
        self.sock.sendto(self.wrap_data(data), self.client_addr)

    def handle_recv(self):
        while True:
            data, src = self.sock.recvfrom(2048)
            self.client_addr = src
            data = self.unwrap_data(data)
            self.tun.write(data)

    def handle_tun_read(self, data):
        self.send_to_client(data)

    def wrap_data(self, data):
        data = self.cipher.encrypt_all(data)
        return data

    def unwrap_data(self, data):
        data, _ = self.cipher.decrypt_all(data)
        return data
