import fcntl
import struct
import os
import threading
import select
import time

from logger import LOGGER

TUNSETIFF = 0x400454ca
TUNSETOWNER = TUNSETIFF + 2
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000


class TUN:
    def __init__(self, name, recv_callback):
        LOGGER.info("TUN init with name: %s" % (name,))
        self.tun = os.open('/dev/net/tun', os.O_RDWR)
        ifr = struct.pack('16sH', name.encode('utf-8'), IFF_TUN | IFF_NO_PI)
        fcntl.ioctl(self.tun, TUNSETIFF, ifr)
        fcntl.ioctl(self.tun, TUNSETOWNER, 1000)
        self.recv_cb = recv_callback
        self.running = False

    def run(self):
        LOGGER.info("TUN run")
        self.running = True
        self.read_thread = threading.Thread(target=self.handle_read)
        self.read_thread.start()

    def stop(self):
        LOGGER.info("TUN stop")
        self.running = False
        while self.read_thread.is_alive():
            time.sleep(1)
        os.close(self.tun)

    def write(self, data):
        LOGGER.debug("TUN write")
        os.write(self.tun, data)

    def handle_read(self):
        LOGGER.info("TUN start read handler")
        while self.running:
            readable, _, _ = select.select([self.tun,], [], [], 1)
            if not readable:
                continue
            data = os.read(self.tun, 2048)
            LOGGER.debug("TUN read")
            if not self.recv_cb:
                continue
            self.recv_cb(data)