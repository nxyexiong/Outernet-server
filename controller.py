import socket
import select
import threading
import time

from cipher import Chacha20Cipher
from server import Server
from profile import Profile
from protocol import (Protocol, CMD_CLIENT_HANDSHAKE, CMD_SERVER_HANDSHAKE,
                      CMD_CLIENT_DATA, CMD_SERVER_DATA)
from logger import LOGGER

CLIENT_TIMEOUT = 12 * 60 * 60  # 12 hours
TIMEOUT_CHECK_INTERVAL = 30 * 60  # half an hour
SAVE_TRAFFIC_CHECK_INTERVAL = 5 * 60  # 5 mins


class Controller:
    def __init__(self, port, secret, db_host, db_user, db_passwd, fee_rate):
        LOGGER.info("Controller init with port: %d, secret: %s" % (port, secret))
        self.fee_rate = fee_rate
        self.profile = Profile(db_host, db_user, db_passwd)
        self.profile.get_conn(is_check=True)  # check if db is ok
        self.ip_list = []
        self.tun_name_list = []
        for i in range(1, 255):
            self.ip_list.append('10.0.0.' + str(i))
            self.tun_name_list.append('tun' + str(i - 1))
        self.id_to_server = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        self.secret = secret
        self.cipher = Chacha20Cipher(secret)
        self.running = False

        self.recv_thread = None
        self.timeout_thread = None
        self.handle_traffic_thread = None

    def run(self):
        LOGGER.info("Controller run")
        self.running = True
        self.recv_thread = threading.Thread(target=self.handle_recv)
        self.recv_thread.start()
        self.timeout_thread = threading.Thread(target=self.handle_timeout)
        self.timeout_thread.start()
        self.handle_traffic_thread = threading.Thread(target=self.handle_traffic)
        self.handle_traffic_thread.start()

    def stop(self):
        LOGGER.info("Controller stop")
        for _, value in self.id_to_server.items():
            value.stop()
        self.running = False
        if self.recv_thread is not None:
            while self.recv_thread.is_alive():
                time.sleep(1)
        self.sock.close()
        if self.timeout_thread is not None:
            while self.timeout_thread.is_alive():
                time.sleep(1)
        if self.handle_traffic_thread is not None:
            while self.handle_traffic_thread.is_alive():
                time.sleep(1)

    def handle_recv(self):
        LOGGER.info("Controller start recv handler")
        while self.running:
            readable, _, _ = select.select([self.sock, ], [], [], 1)
            if not readable:
                continue
            data, addr = self.sock.recvfrom(2048)
            data = self.unwrap_data(data)
            LOGGER.debug("Controller recv")

            if len(data) <= 0:
                continue

            protocol = Protocol()
            if protocol.parse(data) <= 1:
                continue

            if protocol.cmd == CMD_CLIENT_HANDSHAKE:
                self.handle_client_handshake(protocol, addr)
            elif protocol.cmd == CMD_CLIENT_DATA:
                self.handle_client_data(protocol, addr)

    def handle_client_handshake(self, protocol, addr):
        identification = protocol.identification
        if not self.profile.is_id_exist(identification):
            return
        name = self.profile.get_name_by_id(identification)
        traffic_remain = self.profile.get_traffic_remain_by_id(identification)
        if traffic_remain <= 0:
            LOGGER.info("Controller recv client but traffic <= 0, name: %s, traffic_remain: %s" % (name, traffic_remain))
            return
        LOGGER.info("Controller recv client, name: %s, traffic_remain: %s" % (name, traffic_remain))

        server = self.id_to_server.get(identification)
        if server:
            LOGGER.info("Controller get registered client with tun_name: %s, tun_ip: %s, dst_ip: %s" % (server.tun.name, server.tun.tun_ip, server.tun.dst_ip))
            server.client_addr = addr
            protocol = Protocol()
            protocol.cmd = CMD_SERVER_HANDSHAKE
            protocol.tun_ip_raw = self.ip_str_to_raw(server.tun.tun_ip)
            protocol.dst_ip_raw = self.ip_str_to_raw(server.tun.dst_ip)
            self.sock.sendto(self.wrap_data(protocol.get_bytes()), addr)
        else:
            tun_ip = self.alloc_ip()
            dst_ip = self.alloc_ip()
            tun_name = self.alloc_tun_name()
            if not tun_ip or not dst_ip or not tun_name:
                LOGGER.error("Controller tun_ip or dst_ip or tun_name cannot be alloced")
                self.free_ip(tun_ip)
                self.free_ip(dst_ip)
                self.free_tun_name(tun_name)
                return
            server = Server(tun_name, tun_ip, dst_ip, addr, traffic_remain, self.client_send_data_callback)
            server.run()
            LOGGER.info("controller get unregistered client with tun_name: %s, tun_ip: %s, dst_ip: %s" % (tun_name, tun_ip, dst_ip))
            self.id_to_server[identification] = server
            protocol = Protocol()
            protocol.cmd = CMD_SERVER_HANDSHAKE
            protocol.tun_ip_raw = self.ip_str_to_raw(tun_ip)
            protocol.dst_ip_raw = self.ip_str_to_raw(dst_ip)
            self.sock.sendto(self.wrap_data(protocol.get_bytes()), addr)

    def handle_client_data(self, protocol, addr):
        identification = protocol.identification
        if not self.profile.is_id_exist(identification):
            return
        server = self.id_to_server.get(identification)
        if server:
            server.handle_recv(protocol.data, addr)
        else:
            LOGGER.error("Controller recv client, but server is None")

    def client_send_data_callback(self, data, addr):
        protocol = Protocol()
        protocol.cmd = CMD_SERVER_DATA
        protocol.data = data
        self.sock.sendto(self.wrap_data(protocol.get_bytes()), addr)

    def handle_timeout(self):
        LOGGER.info("Controller start timeout handler")
        sec = 0
        while self.running:
            LOGGER.debug("Controller check timeout ticking")
            if (sec < TIMEOUT_CHECK_INTERVAL):
                time.sleep(1)
                sec += 1
                continue
            sec = 0
            LOGGER.info("Controller check timeout")

            for identification, server in self.id_to_server.items():
                now = time.time()
                if now - server.last_active_time > CLIENT_TIMEOUT:
                    LOGGER.info("Controller client timeout with tun: %s" % (server.tun.name,))
                    self.free_ip(server.tun.tun_ip)
                    self.free_ip(server.tun.dst_ip)
                    self.free_tun_name(server.tun.name)
                    server.stop()
                    self.id_to_server.pop(identification)
                    break

    def handle_traffic(self):
        LOGGER.info("Controller start traffic handler")
        sec = 0
        while self.running:
            if sec % SAVE_TRAFFIC_CHECK_INTERVAL == 0:
                LOGGER.info("Controller handle traffic")
                # save server traffic
                for identification, server in self.id_to_server.copy().items():
                    name = self.profile.get_name_by_id(identification)
                    self.profile.minus_traffic_remain_by_id(identification, int(server.traffic_used * self.fee_rate))
                    server.traffic_remain = self.profile.get_traffic_remain_by_id(identification)
                    LOGGER.info("Controller handle traffic name: %s, minus: %s, remain: %s" % (name, server.traffic_used, server.traffic_remain))
                    server.traffic_used = 0
                    if server.traffic_remain <= 0:
                        # release server
                        LOGGER.info("Controller handle traffic releasing server")
                        self.free_ip(server.tun.tun_ip)
                        self.free_ip(server.tun.dst_ip)
                        self.free_tun_name(server.tun.name)
                        server.stop()
                        self.id_to_server.pop(identification)
                # refresh database
                self.profile.refresh_cache()

            time.sleep(1)
            sec += 1

        # save on stop
        for identification, server in self.id_to_server.copy().items():
            self.profile.minus_traffic_remain_by_id(identification, int(server.traffic_used * self.fee_rate))
            server.traffic_remain = self.profile.get_traffic_remain_by_id(identification)

    def alloc_tun_name(self):
        for i in range(0, 255):
            tun_name = 'tun' + str(i)
            if tun_name not in self.tun_name_list:
                continue
            self.tun_name_list.remove(tun_name)
            return tun_name
        return None

    def free_tun_name(self, tun_name):
        if not tun_name:
            return
        self.tun_name_list.append(tun_name)

    def alloc_ip(self):
        for i in range(1, 255):
            ip = '10.0.0.' + str(i)
            if ip not in self.ip_list:
                continue
            self.ip_list.remove(ip)
            return ip
        return None

    def free_ip(self, ip):
        if not ip:
            return
        self.ip_list.append(ip)

    def ip_str_to_raw(self, ip):
        segs = ip.split('.')
        raw_list = []
        for item in segs:
            raw_list.append(int(item))
        return bytes(raw_list)

    def port_int_to_raw(self, port):
        return bytes([port >> 8, port % 256])

    def wrap_data(self, data):
        data = self.cipher.encrypt(data)
        return data

    def unwrap_data(self, data):
        data = self.cipher.decrypt(data)
        return data
