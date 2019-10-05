import sqlite3
import hashlib

DATABASE_FILE = 'profile.db'


class Profile:
    def __init__(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, traffic_remain INTEGER DEFAULT 0);")

    def get_id_list(self):
        id_list = []
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        for item in cursor.execute("SELECT * FROM users"):
            name = item[0]
            identification = hashlib.sha256(name.encode('utf-8')).digest()
            id_list.append(identification)
        conn.close()
        return id_list

    def get_id_map(self):
        id_map = {}
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        for item in cursor.execute("SELECT * FROM users"):
            name = item[0]
            traffic_remain = item[1]
            identification = hashlib.sha256(name.encode('utf-8')).digest()
            id_map[identification] = traffic_remain
        conn.close()
        return id_map

    def is_id_exist(self, identification):
        id_map = self.get_id_map()
        if identification in id_map:
            return True
        return False

    def get_traffic_remain_by_id(self, identification):
        id_map = self.get_id_map()
        return id_map.get(identification, 0)

    def minus_traffic_remain_by_id(self, identification, delta):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        for item in cursor.execute("SELECT * FROM users"):
            name = item[0]
            traffic_remain = item[1]
            identification_db = hashlib.sha256(name.encode('utf-8')).digest()
            if (identification == identification_db):
                traffic_remain -= delta
                cursor.execute("UPDATE users SET traffic_remain=%s WHERE name=%s" % (str(traffic_remain), name))
                conn.close()
                return True
        conn.close()
        return False
