import os
import threading
import socket
import select
import time

from cipher import Chacha20Cipher
from tun import TUN
from logger import LOGGER

class Relay:
    def __init__(self, controller_sock, secret, client_addr, relay_server, relay_port, relay_identification):
        LOGGER.info("Relay init with secret: %s, client_addr: %s" % (secret, client_addr))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.cipher = Chacha20Cipher(secret)
        self.client_addr = client_addr
        self.running = False
        self.last_active_time = time.time()
        # relay
        self.controller_sock = controller_sock
        self.relay_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.relay_sock.bind(('', 0))
        self.relay_server_addr = (relay_server, relay_port)
        self.relay_identification = relay_identification
        self.relay_tun_ip_raw = None
        self.relay_dst_ip_raw = None
        self.handshaked = False

    def run(self):
        LOGGER.info("Relay run")
        self.running = True
        self.recv_thread = threading.Thread(target=self.handle_recv)
        self.recv_thread.start()
        self.relay_handshake_thread = threading.Thread(target=self.handle_relay_handshake)
        self.relay_handshake_thread.start()

    def stop(self):
        LOGGER.info("Relay stop")
        self.running = False
        while self.recv_thread.is_alive():
            time.sleep(1)
        while self.relay_handshake_thread.is_alive():
            time.sleep(1)
        while self.relay_recv_thread is not None and self.relay_recv_thread.is_alive():
            time.sleep(1)
        self.sock.close()
        self.relay_sock.close()

    def handle_relay_handshake(self):
        LOGGER.debug("Relay handle_relay_handshake")
        send_data = b'\x01' + self.relay_identification
        while self.running:
            self.relay_sock.sendto(self.wrap_data(send_data), self.relay_server_addr)
            try:
                self.relay_sock.settimeout(5)
                data, _ = self.relay_sock.recvfrom(2048)
                self.relay_sock.settimeout(None)
            except socket.timeout:
                LOGGER.warning("Relay handshake timeout")
                continue
            data = self.unwrap_data(data)
            if len(data) != 11 or data[0] != 0x01:
                continue
            LOGGER.debug("Relay handshake recved")
            tun_ip_raw = data[1:5]
            dst_ip_raw = data[5:9]
            port = data[9] * 256 + data[10]
            self.relay_server_addr = (self.relay_server_addr[0], port)
            self.relay_tun_ip_raw = tun_ip_raw
            self.relay_dst_ip_raw = dst_ip_raw
            self.relay_recv_thread = threading.Thread(target=self.handle_relay_recv)
            self.relay_recv_thread.start()
            self.send_handshake_reply(self.controller_sock)
            self.handshaked = True
            break

    def send_handshake_reply(self, sock):
        if not self.handshaked:
            return
        port = self.sock.getsockname()[1]
        port_raw = bytes([port >> 8, port % 256])
        send_data = b'\x01' + self.relay_tun_ip_raw + self.relay_dst_ip_raw + port_raw
        sock.sendto(self.wrap_data(send_data), self.client_addr)

    def send_to_client(self, data):
        LOGGER.debug("Relay send to client")
        if not self.handshaked:
            return
        if not self.client_addr:
            return
        send_data = self.wrap_data(data)
        self.sock.sendto(send_data, self.client_addr)

    def send_to_relay(self, data):
        LOGGER.debug("Relay send to relay")
        if not self.handshaked:
            return
        if not self.relay_server_addr:
            return
        send_data = self.wrap_data(data)
        self.relay_sock.sendto(send_data, self.relay_server_addr)

    def handle_recv(self):
        LOGGER.info("Relay start recv handler")
        while self.running:
            readable, _, _ = select.select([self.sock,], [], [], 1)
            if not readable:
                continue
            data, src = self.sock.recvfrom(2048)
            LOGGER.debug("Relay recv data")
            self.last_active_time = time.time()  # only update when client 
            self.client_addr = src  # avoid ip changing of client
            data = self.unwrap_data(data)
            self.send_to_relay(data)

    def handle_relay_recv(self):
        LOGGER.info("Relay start recv handler")
        while self.running:
            readable, _, _ = select.select([self.relay_sock,], [], [], 1)
            if not readable:
                continue
            data, _ = self.relay_sock.recvfrom(2048)
            LOGGER.debug("Relay recv data")
            data = self.unwrap_data(data)
            self.send_to_client(data)

    def wrap_data(self, data):
        data = self.cipher.encrypt(data)
        return data

    def unwrap_data(self, data):
        data = self.cipher.decrypt(data)
        return data
