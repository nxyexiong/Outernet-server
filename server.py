import time

from tun import TUN
from logger import LOGGER


class Server:
    def __init__(self, tun_name, tun_ip, dst_ip, client_addr, traffic_remain, send_data_cb):
        LOGGER.info("Server init with tun_name: %s, tun_ip: %s, dst_ip: %s, client_addr: %s" % (tun_name, tun_ip, dst_ip, client_addr))
        self.tun = TUN(tun_name, tun_ip, dst_ip, self.handle_tun_read)
        self.client_addr = client_addr
        self.send_data_cb = send_data_cb
        self.running = False
        self.last_active_time = time.time()
        self.traffic_remain = traffic_remain
        self.traffic_used = 0

        self.recv_thread = None

    def run(self):
        LOGGER.info("Server run")
        self.tun.run()
        self.running = True

    def stop(self):
        LOGGER.info("Server stop")
        self.running = False
        self.tun.stop()

    def send_to_client(self, data):
        LOGGER.debug("Server send to client")
        if not self.running:
            return
        if not self.client_addr:
            return
        self.traffic_used += len(data)
        if self.traffic_remain - self.traffic_used <= 0:
            return
        self.send_data_cb(data, self.client_addr)

    def handle_recv(self, data, addr):
        LOGGER.debug("Server recv data")
        if not self.running:
            return
        self.traffic_used += len(data)
        if self.traffic_remain - self.traffic_used <= 0:
            return
        self.last_active_time = time.time()  # only update when client
        self.client_addr = addr  # avoid ip changing of client
        self.tun.write(data)

    def handle_tun_read(self, data):
        self.send_to_client(data)
