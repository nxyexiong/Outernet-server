import time
import hashlib

from controller import Controller
from logger import LOGGER


if __name__ == "__main__":
    LOGGER.info("start Outernet server")

    id_list_raw = [
        b'nxyexiong'
    ]
    LOGGER.info("start with id list: %s" % (id_list_raw,))

    id_list = []
    for item in id_list_raw:
        id_hash = hashlib.sha256(item).digest()
        id_list.append(id_hash)

    LOGGER.info("start controller")
    controller = Controller(6666, b'nxyexiong', id_list)
    controller.run()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            LOGGER.info("terminating...")
            controller.stop()
            time.sleep(1)
            break

    LOGGER.info("terminated")
    exit(0)
