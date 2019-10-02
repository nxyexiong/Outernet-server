import socket
import select
import threading
import time
import os

from cipher import Chacha20Cipher
from server import Server
from profile_utils import save_traffic
from tuntap_utils import install_tun, uninstall_tun
from logger import LOGGER

CLIENT_TIMEOUT = 12 * 60 * 60  # 12 hours
TIMEOUT_CHECK_INTERVAL = 30 * 60  # half an hour
SAVE_TRAFFIC_CHECK_INTERVAL = 5 * 60  # 5 mins


class Controller:
    def __init__(self, port, secret, id_list):
        LOGGER.info("Controller init with port: %d, secret: %s" % (port, secret))
        self.id_list = id_list
        self.ip_list = []
        self.tun_name_list = []
        for i in range(1, 255):
            self.ip_list.append('10.0.0.' + str(i))
            self.tun_name_list.append('tun' + str(i - 1))
        self.id_to_server = {}
        self.server_to_tun_name = {}
        self.tun_name_to_info = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        self.secret = secret
        self.cipher = Chacha20Cipher(secret)
        self.running = False

    def run(self):
        LOGGER.info("Controller run")
        self.running = True
        self.recv_thread = threading.Thread(target=self.handle_recv)
        self.recv_thread.start()
        self.timeout_thread = threading.Thread(target=self.handle_timeout)
        self.timeout_thread.start()
        self.save_traffic_thread = threading.Thread(target=self.handle_save_traffic)
        self.save_traffic_thread.start()

    def stop(self):
        LOGGER.info("Controller stop")
        for key, value in self.server_to_tun_name.items():
            key.stop()
            uninstall_tun(value)
        self.running = False
        while self.recv_thread.is_alive():
            time.sleep(1)
        self.sock.close()
        while self.timeout_thread.is_alive():
            time.sleep(1)

    def handle_recv(self):
        LOGGER.info("Controller start recv handler")
        while self.running:
            readable, _, _ = select.select([self.sock,], [], [], 1)
            if not readable:
                continue
            data, addr = self.sock.recvfrom(2048)
            data = self.unwrap_data(data)
            LOGGER.info("Controller recv")

            if len(data) <= 0:
                continue

            if data[0] != 0x01:
                time.sleep(0.5)  # avoid ddos
                continue

            identification = data[1:33]
            if identification not in self.id_list:
                continue

            server = self.id_to_server.get(identification)
            if server:
                tun_name = self.server_to_tun_name.get(server)
                if not tun_name:
                    LOGGER.warn("Controller tun_name not found")
                    server.stop()
                    self.id_to_server.pop(identification)
                    continue
                tun_info = self.tun_name_to_info.get(tun_name)
                if not tun_info:
                    LOGGER.warn("Controller tun_info not found")
                    self.server_to_tun_name.pop(server)
                    server.stop()
                    self.id_to_server.pop(identification)
                    continue
                LOGGER.info("Controller get registered client with tun_name: %s, tun_ip: %s, dst_ip: %s, port: %d" % (tun_name, tun_info[0], tun_info[1], tun_info[2]))
                server.client_addr = addr
                tun_ip_raw = self.ip_str_to_raw(tun_info[0])
                dst_ip_raw = self.ip_str_to_raw(tun_info[1])
                port_raw = self.port_int_to_raw(tun_info[2])
                send_data = b'\x01' + tun_ip_raw + dst_ip_raw + port_raw
                self.sock.sendto(self.wrap_data(send_data), addr)
            else:
                tun_ip = self.alloc_ip()
                dst_ip = self.alloc_ip()
                tun_name = self.alloc_tun_name()
                if not tun_ip or not dst_ip or not tun_name:
                    LOGGER.error("Controller tun_ip or dst_ip or tun_name cannot be alloced")
                    self.free_ip(tun_ip)
                    self.free_ip(dst_ip)
                    self.free_tun_name(tun_name)
                    time.sleep(0.5)
                    continue
                install_tun(tun_name, tun_ip, dst_ip)
                server = Server(self.secret, tun_name, addr)
                server.run()
                port = server.sock.getsockname()[1]
                port_raw = self.port_int_to_raw(port)
                LOGGER.info("controller get unregistered client with tun_name: %s, tun_ip: %s, dst_ip: %s, port: %d" % (tun_name, tun_ip, dst_ip, port))
                self.id_to_server[identification] = server
                self.server_to_tun_name[server] = tun_name
                self.tun_name_to_info[tun_name] = (tun_ip, dst_ip, port)
                tun_ip_raw = self.ip_str_to_raw(tun_ip)
                dst_ip_raw = self.ip_str_to_raw(dst_ip)
                send_data = b'\x01' + tun_ip_raw + dst_ip_raw + port_raw
                self.sock.sendto(self.wrap_data(send_data), addr)

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
                tun_name = self.server_to_tun_name.get(server)
                if not tun_name:
                    LOGGER.error("Controller timeout tun_name not found")
                    server.stop()
                    self.id_to_server.pop(identification)
                    break
                tun_info = self.tun_name_to_info.get(tun_name)
                if not tun_info:
                    LOGGER.error("Controller timeout tun_info not found")
                    self.server_to_tun_name.pop(server)
                    server.stop()
                    self.id_to_server.pop(identification)
                    break
                if now - server.last_active_time > CLIENT_TIMEOUT:
                    LOGGER.info("Controller client timeout with tun_info: %s" % (tun_info,))
                    self.tun_name_to_info.pop(tun_name)
                    self.free_ip(tun_info[0])
                    self.free_ip(tun_info[1])
                    self.free_tun_name(tun_name)
                    self.server_to_tun_name.pop(server)
                    server.stop()
                    uninstall_tun(tun_name)
                    self.id_to_server.pop(identification)
                    break

    def handle_save_traffic(self):
        LOGGER.info("Controller start save traffic handler")
        sec = 0
        while self.running:
            LOGGER.debug("Controller save traffic ticking")
            if (sec < SAVE_TRAFFIC_CHECK_INTERVAL):
                time.sleep(1)
                sec += 1
                continue
            sec = 0
            LOGGER.info("Controller save traffic")
            traffic_map = {}
            for identification, server in self.id_to_server.items():
                traffic_map[identification] = {}
                traffic_map[identification]['tx'] = server.tx
                traffic_map[identification]['rx'] = server.rx
                server.tx = 0
                server.rx = 0
            save_traffic(traffic_map)

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
            