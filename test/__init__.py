import logging
import unittest


def run_test():
    fmt = '%(asctime)-15s [%(levelname)s] %(message)s'
    # logging.basicConfig(format=fmt, level=logging.DEBUG)

    OPHYD_LOGGER = 'ophyd_session'
    logger = logging.getLogger(OPHYD_LOGGER)
    logger.setLevel(logging.INFO)

    unittest.main()
