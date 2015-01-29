from __future__ import print_function

import logging
import unittest
import time

import numpy as np
from numpy.testing import assert_array_equal

import epics

from ophyd.controls.signal import EpicsSignal
from ophyd.controls.cas import (CasFunction, caServer)

server = None
logger = logging.getLogger(__name__)


@CasFunction()
def async_func(a=0, b=0.0, **kwargs):
    time.sleep(0.5)

    return a + b


@CasFunction(async=False, prefix='test:sync:')
def sync_func(a=0, b=0.0, **kwargs):
    return a * b


@CasFunction(return_value='test')
def string_func(value='test'):
    return value.upper()


@CasFunction(type_=np.int32, count=10)
def array_func(value=0.0):

    return np.arange(10) * value


@CasFunction(type_=np.int32, count=10,
             async=False)
def no_arg_func():
    return np.arange(10)


@CasFunction()
def array_input_func(value=np.array([1., 2., 3.], dtype=np.float)):
    return np.average(value)


@CasFunction()
def failure_func():
    raise ValueError('failed, somehow')


@CasFunction(return_value=True)
def bool_func(bool_one=False, bool_two=True):
    return bool(bool_one or bool_two)


# Can't use positional arguments:
try:
    @CasFunction(prefix='test:')
    def test1(a, b=1):
        pass
except ValueError:
    logger.debug('(Failed as expected)')
else:
    raise ValueError('')


# Can't use variable arguments:
try:
    @CasFunction(prefix='test:')
    def test2(a=1, *b):
        pass
except ValueError:
    logger.debug('(Failed as expected)')


@CasFunction(use_process=False)
def no_process(a=0, b=0.0, **kwargs):
    return a + b


def setUpModule():
    global server
    server = caServer('OPHYD_TEST_CAS_')


def tearDownModule():
    epics.ca.destroy_context()

    logger.debug('Cleaning up')
    server.cleanup()
    logger.info('Done')


class CASFuncTest(unittest.TestCase):
    def test_async(self):
        pvnames = async_func.get_pvnames()

        sig_a = EpicsSignal(pvnames['a'])
        sig_b = EpicsSignal(pvnames['b'])
        sig_proc = EpicsSignal(pvnames['process'])
        sig_ret = EpicsSignal(pvnames['retval'])

        a, b = 3.0, 4.0

        sig_a.value = a
        sig_b.value = b
        sig_proc.put(1, wait=True)

        time.sleep(0.1)

        ca_value = sig_ret.value
        n_val = async_func(a=a, b=b)
        self.assertEquals(ca_value, n_val)
        self.assertEquals(ca_value, a + b)

    def test_sync(self):
        pvnames = sync_func.get_pvnames()

        sig_a = EpicsSignal(pvnames['a'])
        sig_b = EpicsSignal(pvnames['b'])
        sig_proc = EpicsSignal(pvnames['process'])
        sig_ret = EpicsSignal(pvnames['retval'])

        a, b = 3.0, 4.0
        sig_a.value = a
        sig_b.value = b
        sig_proc.value = 1

        time.sleep(0.2)

        ca_value = sig_ret.value
        n_val = sync_func(a=a, b=b)
        self.assertEquals(ca_value, n_val)
        self.assertEquals(ca_value, a * b)

    def test_string(self):
        pvnames = string_func.get_pvnames()

        sig_value = EpicsSignal(pvnames['value'])
        sig_proc = EpicsSignal(pvnames['process'])
        sig_ret = EpicsSignal(pvnames['retval'])

        sig_value.value = 'hello'
        sig_proc.value = 1

        time.sleep(0.2)
        ca_value = sig_ret.value
        n_val = string_func(value='hello')
        self.assertEquals(ca_value, n_val)
        self.assertEquals(ca_value, 'HELLO')

    def test_array(self):
        pvnames = array_func.get_pvnames()

        sig_value = EpicsSignal(pvnames['value'])
        sig_proc = EpicsSignal(pvnames['process'])
        sig_ret = EpicsSignal(pvnames['retval'])

        sig_value.value = 2.0
        sig_proc.value = 1

        time.sleep(0.2)

        ca_value = sig_ret.value
        n_val = array_func(value=2.0)
        assert_array_equal(ca_value, n_val)
        assert_array_equal(ca_value, np.arange(10) * 2.0)

    def test_array_input(self):
        pvnames = array_input_func.get_pvnames()

        sig_value = EpicsSignal(pvnames['value'])
        sig_proc = EpicsSignal(pvnames['process'])
        sig_ret = EpicsSignal(pvnames['retval'])

        input_ = np.array([5, 10, 15])
        sig_value.value = input_
        sig_proc.value = 1

        time.sleep(0.2)
        ca_value = sig_ret.value
        n_val = array_input_func(value=input_)
        assert_array_equal(ca_value, n_val)
        assert_array_equal(ca_value, np.average(input_))

    def test_no_arg(self):
        pvnames = no_arg_func.get_pvnames()

        sig_proc = EpicsSignal(pvnames['process'])
        sig_ret = EpicsSignal(pvnames['retval'])

        sig_proc.value = 1

        time.sleep(0.2)
        ca_value = sig_ret.value
        n_val = no_arg_func()
        assert_array_equal(ca_value, n_val)
        assert_array_equal(ca_value, np.arange(10))

    def test_failure(self):
        pvnames = failure_func.get_pvnames()

        sig_proc = EpicsSignal(pvnames['process'])
        sig_status = EpicsSignal(pvnames['status'])

        sig_proc.value = 1

        time.sleep(0.2)

        self.assertNotEqual(sig_status.value, '')

    def test_bool(self):
        pvnames = bool_func.get_pvnames()

        sig_bool1 = EpicsSignal(pvnames['bool_one'])
        sig_bool2 = EpicsSignal(pvnames['bool_two'])
        sig_proc = EpicsSignal(pvnames['process'])
        EpicsSignal(pvnames['status'])
        sig_ret = EpicsSignal(pvnames['retval'])

        one, two = True, False
        sig_bool1.value = one
        sig_bool2.value = two
        sig_proc.value = 1

        time.sleep(0.2)

        ca_value = sig_ret.value
        n_val = bool_func(bool_one=one, bool_two=two)
        self.assertEquals(ca_value, n_val)
        self.assertEquals(ca_value, True)
        self.assertEquals(sig_ret.get(as_string=True), 'True')

        one, two = False, False
        sig_bool1.value = one
        sig_bool2.value = two
        sig_proc.value = 1

        time.sleep(0.2)

        ca_value = sig_ret.value
        n_val = bool_func(bool_one=one, bool_two=two)
        self.assertEquals(ca_value, n_val)
        self.assertEquals(ca_value, False)
        self.assertEquals(sig_ret.get(as_string=True), 'False')

    def test_no_process(self):
        pvnames = no_process.get_pvnames()

        sig_a = EpicsSignal(pvnames['a'])
        sig_b = EpicsSignal(pvnames['b'])
        sig_ret = EpicsSignal(pvnames['retval'])

        sig_a.value = 3.0
        sig_b.value = 4.0
        time.sleep(0.2)

        self.assertEquals(sig_ret.value, 7.0)
        sig_b.value = 5.0
        time.sleep(0.2)
        self.assertEquals(sig_ret.value, 8.0)

    def test_pvi(self):
        pvi = no_process.get_pv('a')


if __name__ == '__main__':
    fmt = '%(asctime)-15s [%(levelname)s] %(message)s'
    logging.basicConfig(format=fmt, level=logging.DEBUG)

    unittest.main()