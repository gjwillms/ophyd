from __future__ import print_function
import logging
import unittest

from numpy.testing import assert_array_equal

server = None
logger = logging.getLogger(__name__)
session = get_session_manager()


def setUpModule():
    pass


def tearDownModule():
    pass


class UtilsTest(unittest.TestCase):
    def test_1d(self):
        pass


from . import main
is_main = (__name__ == '__main__')
main(is_main)
