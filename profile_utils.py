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
#     b'some_raw_id': 0,
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
            traffic[user_map[key]] = 0
        traffic[user_map[key]] = traffic_map[key]

    try:
        f = open(TRAFFIC_FILE, 'w+')
        yaml.dump(traffic, f)
        return True
    except Exception:
        LOGGER.error('error writing traffic')
        return False


def load_traffic():
    try:
        traffic_map = {}
        users = yaml.load(open(USERS_FILE))['users']
        user_to_id = {}
        for item in users:
            identification = hashlib.sha256(item.encode('utf-8')).digest()
            user_to_id[item] = identification
            traffic_map[identification] = 0
        
        traffics = yaml.load(open(TRAFFIC_FILE))
        for key, value in traffics.items():
            identification = user_to_id.get(key)
            if identification:
                traffic_map[identification] = value

        return traffic_map
    except Exception:
        LOGGER.error('error loading traffic')
        return None
