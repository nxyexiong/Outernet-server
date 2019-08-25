import socket
import threading

from lru import LRU

CACHE_SIZE = 128

class UDPGW:
    def __init__(self, recv_callback):
        self.cache = LRU(CACHE_SIZE)
        self.send_local = recv_callback

    def destroy(self):
        self.running = False

    def run(self):
        self.running = True
        self.thread = threading.Thread(target=self.recv_remote)
        self.thread.start()

    def recv_local(self, data):
        pass

    def send_remote(self, data):
        pass

    def recv_remote(self):
        while self.running:
            pass
        