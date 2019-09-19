import yaml
import hashlib

from logger import LOGGER

USERS_FILE = 'user.yaml'
TRAFFIC_FILE = 'traffic.yaml'


# in USERS_FILE:
# {
#   users: [
#     'aaaa',
#     'bbbb',
#   ]
# }
def load_identifications():
    try:
        users = yaml.load(open(USERS_FILE))['users']
        identifications = []
        for item in users:
            identification = hashlib.sha256(item.encode('utf-8')).digest()
            identifications.append(identification)
        return identifications
    except Exception:
        LOGGER.error('missing user file or format incorrect')
        return None


# traffic_map = {
#     b'some_raw_id': {
#         'rx': 0,
#         'tx': 0,
#     },
#     ...
# }
def save_traffic(traffic_map):
    traffic = {}
    try:
        traffic = yaml.load(open(TRAFFIC_FILE))
    except Exception:
        pass

    user_list = None
    try:
        user_list = yaml.load(open(USERS_FILE))['users']
    except Exception:
        return False

    user_map = {}
    for item in user_list:
        key = hashlib.sha256(item.encode('utf-8')).digest()
        user_map[key] = item

    for key in traffic_map:
        if user_map[key] not in traffic:
            traffic[user_map[key]] = {}
            traffic[user_map[key]]['tx'] = 0
            traffic[user_map[key]]['rx'] = 0
        traffic[user_map[key]]['tx'] += traffic_map[key]['tx']
        traffic[user_map[key]]['rx'] += traffic_map[key]['rx']

    try:
        f = open(TRAFFIC_FILE, 'w+')
        yaml.dump(traffic, f)
        return True
    except Exception:
        LOGGER.error('error writing traffic')
        return False
