import time
import sys

from tuntap_utils import init_tun, uninit_tun
from controller import Controller
from logger import LOGGER


if __name__ == "__main__":
    # check params
    args = sys.argv
    port = None
    secret = None
    db_host = None
    db_user = None
    db_passwd = None
    is_relay = False
    relay_server = None
    relay_port = None
    if len(args) < 6:
        LOGGER.error("wrong parameter count")
        sys.exit(1)
    if '-relay' in args and len(args) < 9:
        LOGGER.error("wrong relay parameter count")
        sys.exit(1)
    try:
        port = int(args[1])
        secret = str(args[2]).encode('utf-8')
        db_host = str(args[3])
        db_user = str(args[4])
        db_passwd = str(args[5])
        if '-relay' in args:
            is_relay = True
            relay_server = str(args[7])
            relay_port = int(args[8])
    except Exception:
        LOGGER.error("wrong parameter type")
        sys.exit(1)

    # start server
    LOGGER.info("start Outernet server")

    init_tun()

    LOGGER.info("start controller")
    controller = Controller(port, secret, db_host, db_user, db_passwd)
    if is_relay:
        controller.set_relay(relay_server, relay_port)
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
