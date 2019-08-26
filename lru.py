class LRU:
    def __init__(self, size, pop_callback):
        self.size = size
        self.map = {}
        self.pop_callback = pop_callback

    def set(self, key, value):
        self.map[key] = value
        self.update(key)
        if len(self.map) > self.size:
            self.pop(list(self.map.keys())[0])

    def get(self, key):
        ret = self.map.get(key)
        if ret:
            self.update(key)
        return ret

    def pop(self, key):
        if self.pop_callback != None:
            self.pop_callback(key, self.map.get(key))
        self.map.pop(key)

    def update(self, key):
        try:
            value = self.map.get(key)
            self.pop(key)
            self.map[key] = value
        except Exception:
            return