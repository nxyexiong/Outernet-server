import os

def open_read_pipe(path):
    try:
        fifo = os.mkfifo(path, 0o666)
    except OSError as e:
        # errno 17: already exists
        if e.errno != 17:
            print(e)
    return os.open(fifo, os.O_RDONLY)

def open_write_pipe(path):
    try:
        fifo = os.mkfifo(path, 0o666)
    except OSError as e:
        # errno 17: already exists
        if e.errno != 17:
            print(e)
    return os.open(fifo, os.O_WRONLY)

def get_ip_type(data):
    if data[0] & 0xf0 == 0x40:
        return 4
    elif data[0] & 0xf0 == 0x60:
        return 6
    else:
        return None

def get_src_from_ipv4(data):
    return data[12:16]

def get_dst_from_ipv4(data):
    return data[16:20]
