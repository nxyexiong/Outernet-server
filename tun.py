import fcntl
import struct
import os
import threading

TUNSETIFF = 0x400454ca
TUNSETOWNER = TUNSETIFF + 2
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000


class TUN:
    def __init__(self, name, recv_callback):
        self.tun = os.open('/dev/net/tun', os.O_RDWR)
        ifr = struct.pack('16sH', name.encode('utf-8'), IFF_TUN | IFF_NO_PI)
        fcntl.ioctl(self.tun, TUNSETIFF, ifr)
        fcntl.ioctl(self.tun, TUNSETOWNER, 1000)
        self.recv_cb = recv_callback

    def run(self):
        self.read_thread = threading.Thread(target=self.handle_read)
        self.read_thread.start()

    def write(self, data):
        os.write(self.tun, data)

    def handle_read(self):
        while True:
            data = os.read(self.tun, 2048)
            if not self.recv_cb:
                continue
            self.recv_cb(data)