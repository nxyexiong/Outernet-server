import socket
import threading
import time
import os

from cipher import AESCipher
from server import Server

CLIENT_TIMEOUT = 24 * 60 * 60  # 1 day
TIMEOUT_CHECK_INTERVAL = 30 * 60  # half an hour


class Controller:
    def __init__(self, port, secret, id_list):
        self.id_list = id_list
        self.ip_list = []
        self.tun_name_list = []
        for i in range(1, 255):
            self.ip_list.append('10.0.0.' + str(i))
        self.id_to_server = {}
        self.server_to_tun_name = {}
        self.tun_name_to_info = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        self.secret = secret
        self.cipher = AESCipher(secret)
        self.running = False

    def run(self):
        print("controller run")
        self.running = True
        self.recv_thread = threading.Thread(target=self.handle_recv)
        self.recv_thread.start()
        self.timeout_thread = threading.Thread(target=self.handle_timeout)
        self.timeout_thread.start()

    def stop(self):
        print("controller stop")
        self.running = False
        self.sock.close()
        for key, value in self.server_to_tun_name:
            key.stop()
            os.system('./uninstall.sh ' + value)

    def handle_recv(self):
        while self.running:
            data, addr = self.sock.recvfrom(2048)
            data = self.unwrap_data(data)
            print("controller recv")

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
                    print("error tun_name not found")
                    server.stop()
                    self.id_to_server.pop(identification)
                    continue
                tun_info = self.tun_name_to_info.get(tun_name)
                if not tun_info:
                    print("error tun_info not found")
                    self.server_to_tun_name.pop(server)
                    server.stop()
                    self.id_to_server.pop(identification)
                    continue
                print("controller get registered client")
                server.client_addr = addr
                tun_ip_raw = self.ip_str_to_raw(tun_info[0])
                dst_ip_raw = self.ip_str_to_raw(tun_info[1])
                port_raw = self.port_int_to_raw(tun_info[2])
                send_data = b'\x01' + tun_ip_raw + dst_ip_raw + port_raw
                self.sock.sendto(send_data, addr)
            else:
                tun_ip = self.alloc_ip()
                dst_ip = self.alloc_ip()
                tun_name = self.alloc_tun_name()
                if not tun_ip or not dst_ip or not tun_name:
                    self.free_ip(tun_ip)
                    self.free_ip(dst_ip)
                    self.free_tun_name(tun_name)
                    time.sleep(0.5)
                    continue
                print("controller get unregistered client")
                os.system("./install.sh " + tun_name + " " + tun_ip + " " + dst_ip)
                server = Server(self.secret, tun_name, addr)
                server.run()
                port = server.sock.getsockname()[1]
                port_raw = self.port_int_to_raw(port)
                self.id_to_server[identification] = server
                self.server_to_tun_name[server] = tun_name
                self.tun_name_to_info[tun_name] = (tun_ip, dst_ip, port)
                tun_ip_raw = self.ip_str_to_raw(tun_ip)
                dst_ip_raw = self.ip_str_to_raw(dst_ip)
                send_data = b'\x01' + tun_ip_raw + dst_ip_raw + port_raw
                self.sock.sendto(send_data, addr)

    def handle_timeout(self):
        while self.running:
            for identification, server in self.id_to_server:
                now = time.time()
                tun_name = self.server_to_tun_name.get(server)
                if not tun_name:
                    print("timeout: error tun_name not found")
                    server.stop()
                    self.id_to_server.pop(identification)
                    break
                tun_info = self.tun_name_to_info.get(tun_name)
                if not tun_info:
                    print("timeout: error tun_info not found")
                    self.server_to_tun_name.pop(server)
                    server.stop()
                    self.id_to_server.pop(identification)
                    break
                if server.last_active_time - now > CLIENT_TIMEOUT:
                    print("timeout: client timeout")
                    self.tun_name_to_info.pop(tun_name)
                    self.free_ip(tun_info[0])
                    self.free_ip(tun_info[1])
                    self.free_tun_name(tun_name)
                    self.server_to_tun_name.pop(server)
                    server.stop()
                    self.id_to_server.pop(identification)
                    break
            time.sleep(TIMEOUT_CHECK_INTERVAL)

    def alloc_tun_name(self):
        for i in range(0, 255):
            tun_name = 'tun' + str(i)
            if tun_name in self.tun_name_list:
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
        data = self.cipher.encrypt_all(data)
        return data

    def unwrap_data(self, data):
        data, _ = self.cipher.decrypt_all(data)
        return data
            