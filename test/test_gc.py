from __future__ import print_function

import logging
import unittest
import time

import weakref
import gc

from ophyd.utils.epics_pvs import record_field
from ophyd.controls import (EpicsSignal, EpicsMotor, PVPositioner)
from ophyd.utils.weak_method import FunctionProxy
from ophyd import get_session_manager


logger = logging.getLogger(__name__)

motor_rec = 'XF:31IDA-OP{Tbl-Ax:X1}Mtr'
session_mgr = None


def setUpModule():
    global session_mgr

    session_mgr = get_session_manager()


def tearDownModule():
    pass


class GCTests(unittest.TestCase):
    def check_refs(self, ref, quiet=False):
        gc.collect()

        if ref() is not None:
            if not quiet:
                logger.debug("signal was not gc'd:")
                for i, referrer in enumerate(gc.get_referrers(ref())):
                    logger.debug('referrer {} {}'.format(i, referrer))
                    logger.debug('')

                for i, referent in enumerate(gc.get_referents(ref())):
                    logger.debug('referent {} {}'.format(i, referent))
                    logger.debug('')

            self.fail('Garbage collection failed for: {}'.format(ref()))
        else:
            logger.debug('%r removed OK' % ref)

    def test_function_proxy(self):
        class A(object):
            def fcn(self):
                return 1

        # test instance methods
        a = A()
        wmp = FunctionProxy(a.fcn, quiet=False)

        self.assertEquals(wmp(), 1)

        del a

        try:
            wmp()
        except ReferenceError:
            pass
        else:
            self.fail('Method proxy did not raise referenceerror')

        # test regular functions
        def fcn(*args):
            return sum(args)

        wmp = FunctionProxy(fcn, quiet=False)
        self.assertEquals(wmp(1, 2, 3), 6)

        del fcn

        try:
            wmp(1, 2, 3)
        except ReferenceError:
            pass
        else:
            self.fail('Function proxy did not raise referenceerror')

    def test_epicssignal_wait_connected(self):
        pv_name = record_field(motor_rec, 'STOP')
        test_signal = EpicsSignal(pv_name, name='test_signal')

        def cb_fcn(**kwargs):
            pass

        test_signal.subscribe(cb_fcn)

        time.sleep(1.0)

        r = weakref.ref(test_signal)
        del session_mgr['test_signal']
        del test_signal

        self.check_refs(r)

    def test_epicssignal_nowait(self):
        pv_name = record_field(motor_rec, 'STOP')
        test_signal = EpicsSignal(pv_name, name='test_signal')

        def cb_fcn(**kwargs):
            pass

        test_signal.subscribe(cb_fcn, weak=True)

        # callback removal should also trigger removal from ophydobject list
        del cb_fcn

        sub = test_signal._default_sub
        self.assertEqual(len(test_signal._subs[sub]), 0,
                        'WeakRef subscription not removed')

        r = weakref.ref(test_signal)
        del session_mgr['test_signal']
        del test_signal

        self.check_refs(r)

    def test_epicsmotor(self):
        test_motor = EpicsMotor(motor_rec, name='test_motor')

        time.sleep(1.0)
        r = weakref.ref(test_motor)

        try:
            self.check_refs(r, quiet=True)
        except AssertionError:
            pass
        else:
            self.fail('check_ref not working as expected')

        del session_mgr['test_motor']
        del test_motor

        self.check_refs(r)

    def test_pvpositioner(self):
        pos = PVPositioner(record_field(motor_rec, 'VAL'),
                           readback=record_field(motor_rec, 'RBV'),
                           done=record_field(motor_rec, 'MOVN'), done_val=0,
                           put_complete=True,
                           name='pos',
                           )

        time.sleep(1.0)

        r = weakref.ref(pos)

        def cb_fcn(**kwargs):
            pass

        pos.subscribe(cb_fcn)

        del session_mgr['pos']
        del pos

        self.check_refs(r)


if __name__ == '__main__':
    fmt = '%(asctime)-15s [%(levelname)s] %(message)s'
    logging.basicConfig(format=fmt, level=logging.DEBUG)

    unittest.main()
