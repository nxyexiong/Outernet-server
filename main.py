import time

from tuntap_utils import init_tun, uninit_tun
from controller import Controller
from profile_utils import load_identifications
from logger import LOGGER


if __name__ == "__main__":
    LOGGER.info("start Outernet server")

    init_tun()

    id_list = load_identifications()

    LOGGER.info("start controller")
    controller = Controller(6666, b'nxyexiong', id_list)
    controller.run()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            LOGGER.info("terminating...")
            controller.stop()
            break

    uninit_tun()

    LOGGER.info("terminated")
