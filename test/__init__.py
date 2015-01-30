import logging
import unittest
from ophyd.controls.cas import caServer

caserver = None


def get_caserver():
    global caserver

    if caserver is None:
        caserver = caServer('__TESTING__')

    return caserver


def run_test():
    # fmt = '%(asctime)-15s [%(levelname)s] %(message)s'
    # logging.basicConfig(format=fmt, level=logging.DEBUG)

    OPHYD_LOGGER = 'ophyd_session'
    logger = logging.getLogger(OPHYD_LOGGER)
    logger.setLevel(logging.INFO)

    unittest.main()
