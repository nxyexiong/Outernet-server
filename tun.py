import fcntl
import struct
import os
import threading
import select
import time

from tuntap_utils import install_tun, uninstall_tun
from logger import LOGGER

TUNSETIFF = 0x400454ca
TUNSETOWNER = TUNSETIFF + 2
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000


class TUN:
    def __init__(self, name, tun_ip, dst_ip, recv_callback):
        LOGGER.info("TUN init with name: %s, tun_ip: %s, dst_ip: %s" % (name, tun_ip, dst_ip))
        self.name = name
        self.tun_ip = tun_ip
        self.dst_ip = dst_ip

        self.recv_cb = recv_callback
        self.running = False

        self.run_thread = None

    def run(self):
        LOGGER.info("TUN run")
        self.run_thread = threading.Thread(target=self.handle_run)
        self.run_thread.start()

    def handle_run(self):
        install_tun(self.name, self.tun_ip, self.dst_ip)
        self.tun = os.open('/dev/net/tun', os.O_RDWR)
        ifr = struct.pack('16sH', self.name.encode('utf-8'), IFF_TUN | IFF_NO_PI)
        fcntl.ioctl(self.tun, TUNSETIFF, ifr)
        fcntl.ioctl(self.tun, TUNSETOWNER, 1000)
        self.running = True
        self.handle_read()
        os.close(self.tun)
        uninstall_tun(self.name)

    def stop(self):
        LOGGER.info("TUN stop")
        self.running = False
        if self.run_thread is not None:
            while self.run_thread.is_alive():
                time.sleep(1)

    def write(self, data):
        LOGGER.debug("TUN write")
        os.write(self.tun, data)

    def handle_read(self):
        LOGGER.info("TUN start read handler")
        while self.running:
            readable, _, _ = select.select([self.tun, ], [], [], 1)
            if not readable:
                continue
            data = os.read(self.tun, 2048)
            LOGGER.debug("TUN read")
            if not self.recv_cb:
                continue
            self.recv_cb(data)
