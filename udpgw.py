import socket
import queue
import threading
import select

from lru import LRU
from utils import get_header_length_from_ipv4, get_src_from_ipv4, \
                  get_dst_from_ipv4, get_src_from_udp, get_dst_from_udp, \
                  get_payload_from_udp, sock_addr_to_bytes, sock_bytes_to_addr, \
                  create_ipv4_udp

CACHE_SIZE = 128

class UDPGW:
    def __init__(self, recv_callback):
        self.cache = LRU(CACHE_SIZE, self.lru_pop)  # src to dst
        self.send_local = recv_callback
        self.local_recv_queue = queue.Queue()
        self.remote_list = []  # remote socket list
        self.remote_map = {}   # src to remote socket
        self.dst_to_src = {}   # dst to src

    def destroy(self):
        self.running = False

    def run(self):
        self.running = True
        self.remote_thread = threading.Thread(target=self.handle_recv_remote)
        self.remote_thread.start()
        self.local_thread = threading.Thread(target=self.handle_recv_local)
        self.local_thread.start()

    def recv_local(self, data):
        self.local_recv_queue.put(data)

    def handle_recv_local(self):
        while self.running:
            data = self.local_recv_queue.get()

            ip_header_len = get_header_length_from_ipv4(data)
            ip_src = get_src_from_ipv4(data)
            ip_dst = get_dst_from_ipv4(data)
            udp_data = data[ip_header_len:]
            udp_src = get_src_from_udp(udp_data)
            udp_dst = get_dst_from_udp(udp_data)
            payload = get_payload_from_udp(udp_data)

            src = ip_src + udp_src
            dst = ip_dst + udp_dst

            cache_dst = self.cache.get(src)
            if cache_dst:
                # udp cache hit
                print("udp cache hit, src: " + str(src) + ", remote_map: " + str(self.remote_map) + ", cache: " + str(self.cache.map))
                sock = self.remote_map[src]
                send_addr = sock_bytes_to_addr(dst)
                sock.sendto(payload, send_addr)
            else:
                print("udp cache not hit, src: " + str(src))
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('', 0))
                self.remote_list.append(sock)
                self.cache.set(src, dst)
                self.remote_map[src] = sock
                self.dst_to_src[dst] = src
                send_addr = sock_bytes_to_addr(dst)
                sock.sendto(payload, send_addr)

    def handle_recv_remote(self):
        while self.running:
            recv_socks, _, _ = select.select(self.remote_list, [], [])
            for sock in recv_socks:
                data, addr = sock.recvfrom(65536)
                dst = sock_addr_to_bytes(addr)
                src = self.dst_to_src[dst]
                ip_src = dst[:4]
                udp_src = dst[4:]
                ip_dst = src[:4]
                udp_dst = src[4:]
                packet = create_ipv4_udp(ip_src, ip_dst, udp_src, udp_dst, data)
                self.send_local(packet)

    def lru_pop(self, key, value):
        sock = self.remote_map[key]
        self.remote_list.remove(sock)
        self.remote_map.pop(key)
        self.dst_to_src.pop(value)
        