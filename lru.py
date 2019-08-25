class LRU:
    def __init__(self, size):
        self.size = size
        self.map = {}

    def set(self, key, value):
        self.map[key] = value
        self.update(key)
        if len(self.map) > self.size:
            self.map.pop(list(self.map.keys())[0])

    def get(self, key):
        ret = self.map.get(key)
        if ret:
            self.update(key)
        return ret

    def pop(self, key):
        self.map.pop(key)

    def update(self, key):
        try:
            value = self.map.pop(key)
            self.map[key] = value
        except Exception:
            return