import pymysql
import hashlib


class Profile:
    def __init__(self, host, user, passwd):
        self.host = host
        self.user = user
        self.passwd = passwd
        # users cache
        self.users_cache = []

        conn = self.get_conn()
        if conn is not None:
            conn.cursor().execute("CREATE TABLE IF NOT EXISTS users (name VARCHAR(50) PRIMARY KEY, description VARCHAR(255) DEFAULT '', traffic_remain BIGINT DEFAULT 0);")
            conn.commit()

    def get_conn(self, is_check=False):
        try:
            return pymysql.connect(host=self.host,
                                   user=self.user,
                                   password=self.passwd,
                                   database='outernet',
                                   cursorclass=pymysql.cursors.DictCursor)
        except Exception as err:
            if is_check:
                raise err
            return None

    def refresh_cache(self):
        conn = self.get_conn()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            self.users_cache = cursor.fetchall()
            return True
        return False

    def get_id_list(self):
        if not self.users_cache:
            self.refresh_cache()
        id_list = []
        for item in self.users_cache:
            name = item.get('name')
            identification = hashlib.sha256(name.encode('utf-8')).digest()
            id_list.append(identification)
        return id_list

    def get_id_map(self):
        if not self.users_cache:
            self.refresh_cache()
        id_map = {}
        for item in self.users_cache:
            name = item.get('name')
            traffic_remain = item.get('traffic_remain')
            identification = hashlib.sha256(name.encode('utf-8')).digest()
            id_map[identification] = traffic_remain
        return id_map

    def get_name_by_id(self, identification):
        if not self.users_cache:
            self.refresh_cache()
        for item in self.users_cache:
            name = item.get('name')
            identification_db = hashlib.sha256(name.encode('utf-8')).digest()
            if identification == identification_db:
                return name
        return None

    def is_id_exist(self, identification):
        id_map = self.get_id_map()
        if identification in id_map:
            return True
        return False

    def get_traffic_remain_by_id(self, identification):
        id_map = self.get_id_map()
        return id_map.get(identification, 0)

    def minus_traffic_remain_by_id(self, identification, delta):
        name = self.get_name_by_id(identification)
        if name is None:
            return False
        # write database
        conn = self.get_conn()
        if conn is not None:
            conn.cursor().execute("UPDATE users SET traffic_remain=traffic_remain-%s WHERE name='%s'" % (delta, name))
            conn.commit()
            return True
        return False
