import time
import hashlib

from controller import Controller


if __name__ == "__main__":
    print("start Outernet server")

    id_list_raw = [
        b'nxyexiong'
    ]
    id_list = []

    for item in id_list_raw:
        id_hash = hashlib.sha256(item).digest()
        id_list.append(id_hash)

    controller = Controller(6666, b'nxyexiong', id_list)
    controller.run()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("terminating...")
            controller.stop()
            time.sleep(1)
            break

    print("terminated")
