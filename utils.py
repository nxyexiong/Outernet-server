import os

def open_read_pipe(path):
    try:
        fifo = os.mkfifo(path, 0o666)
    except OSError as e:
        # errno 17: already exists
        if e.errno != 17:
            print(e)
    return os.open(path, os.O_RDONLY)

def open_write_pipe(path):
    try:
        fifo = os.mkfifo(path, 0o666)
    except OSError as e:
        # errno 17: already exists
        if e.errno != 17:
            print(e)
    return os.open(path, os.O_WRONLY)

def get_ip_type(data):
    if data[0] & 0xf0 == 0x40:
        return 4
    elif data[0] & 0xf0 == 0x60:
        return 6
    else:
        return None

def get_header_length_from_ipv4(data):
    return int(data[0] & 0x0f) * 4

def get_src_from_ipv4(data):
    return data[12:16]

def get_dst_from_ipv4(data):
    return data[16:20]

def set_src_to_ipv4(data, src):
    return data[:12] + src + data[16:]

def set_dst_to_ipv4(data, dst):
    return data[:16] + dst + data[20:]

def get_src_from_udp(data):
    return data[0:2]

def get_dst_from_udp(data):
    return data[2:4]

def set_src_to_udp(data, src):
    return src + data[2:]

def set_dst_to_udp(data, dst):
    return data[:2] + dst + data[4:]

def get_payload_from_udp(data):
    length = int(data[4]) * 256 + int(data[5])
    return data[8:length]

def create_ipv4_udp(ip_src, ip_dst, udp_src, udp_dst, payload):
    total_len = 20 + 8 + len(payload)
    udp_len = total_len - 20
    # Version, IHL, DSCP, ECN
    data = b'\x45\x00'
    # Total length
    data += bytes([total_len >> 8, total_len % 256])
    # Identification
    data += b'\x00\x00'
    # Flags, Fragment Offset
    data += b'\x00\x00'
    # Time to live, Protocol
    data += b'\x6e\x11'
    # Header Checksum(set later)
    data += b'\x00\x00'
    # Source addr
    data += ip_src
    # Destination addr
    data += ip_dst

    # calculate ip checksum
    data = data[:10] + wrapsum_16bit(checksum_16bit(data)) + data[12:]

    # udp src
    data += udp_src
    # udp dst
    data += udp_dst
    # udp length
    data += bytes([udp_len >> 8, udp_len % 256])
    # udp checksum(set later)
    data += b'\x00\x00'
    # payload
    data += payload

    # calculate udp checksum
    data = data[:26] + get_udp_checksum(data) + data[28:]

    return data

def get_udp_checksum(data):
    checksum = checksum_16bit(data[12:])
    checksum += 0x11 + len(data[20:])
    if checksum > 0xffff:
        checksum -= 0xffff
    return wrapsum_16bit(checksum)

def checksum_16bit(data):
    length = len(data)
    if length % 2 == 1:
        data += b'\x00'
        length += 1
    length = length >> 1
    checksum = 0x0000
    for i in range(length):
        checksum += int(data[2 * i]) * 256 + int(data[2 * i + 1])
        if checksum > 0xffff:
            checksum -= 0xffff
    return checksum

def wrapsum_16bit(checksum):
    checksum = 0xffff - checksum
    return bytes([checksum >> 8, checksum % 256])

def sock_bytes_to_addr(data):
    host = '.'.join([str(data[0]), str(data[1]), str(data[2]), str(data[3])])
    port = int(data[4]) * 256 + int(data[5])
    return (host, port)

def sock_addr_to_bytes(addr):
    host = addr[0].split('.')
    port = addr[1]
    return bytes([int(host[0]), int(host[1]), int(host[2]), int(host[3]), port >> 8, port % 256])
