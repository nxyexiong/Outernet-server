import os
import threading
import socket
import select
import time

from cipher import AESCipher
from tun import TUN
from logger import LOGGER

class Server:
    def __init__(self, secret, tun_name, client_addr):
        LOGGER.info("Server init with secret: %s, tun_name: %s, client_addr: %s" % (secret, tun_name, client_addr))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.tun = TUN(tun_name, self.handle_tun_read)
        self.cipher = AESCipher(secret)
        self.client_addr = client_addr
        self.running = False
        self.last_active_time = time.time()

    def run(self):
        LOGGER.info("Server run")
        self.running = True
        self.tun.run()
        self.recv_thread = threading.Thread(target=self.handle_recv)
        self.recv_thread.start()

    def stop(self):
        LOGGER.info("Server stop")
        self.running = False
        self.sock.close()
        self.tun.stop()

    def send_to_client(self, data):
        LOGGER.debug("Server send to client")
        if not self.client_addr:
            return
        self.last_active_time = time.time()
        self.sock.sendto(self.wrap_data(data), self.client_addr)

    def handle_recv(self):
        LOGGER.info("Server start recv handler")
        while self.running:
            readable, _, _ = select.select([self.sock,], [], [], timeout=1)
            if not readable:
                continue
            data, src = self.sock.recvfrom(2048)
            LOGGER.debug("Server recv data")
            self.last_active_time = time.time()
            self.client_addr = src  # avoid ip changing of client
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
