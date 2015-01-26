#!/usr/bin/env python2.7
'''A simple test for :class:`EpicsSignal`'''

from __future__ import print_function
import time

import config
from ophyd.controls import (EpicsSignal, Signal)
from ophyd.utils.epics_pvs import record_field


def callback(obj=None, sub_type=None, timestamp=None, value=None, **kwargs):
    logger = config.logger
    logger.info('[callback] [%s] (type=%s) value=%s' % (timestamp, sub_type, value))

    # Test that the monitor dispatcher works (you cannot use channel access in
    # callbacks without it)
    signal = obj
    logger.info('[callback] caget=%s' % signal.get())


def test():
    loggers = ('ophyd.controls.signal',
               'ophyd.session',
               )

    config.setup_loggers(loggers)
    logger = config.logger

    motor_record = config.motor_recs[0]
    val = record_field(motor_record, 'VAL')
    rbv = record_field(motor_record, 'RBV')

    rw_signal = EpicsSignal(rbv, write_pv=val, name='rw_signal')  # put_complete=True)
    rw_signal.subscribe(callback, event_type=rw_signal.SUB_VALUE)
    rw_signal.subscribe(callback, event_type=rw_signal.SUB_SETPOINT)

    rw_signal.value = 2
    time.sleep(1.)
    rw_signal.value = 1
    time.sleep(1.)

    # You can also create a Python Signal:
    testing0 = Signal(name='testing0', value=10)
    logger.info('Python signal: %s' % testing0)

    # Even one with a separate setpoint/readback value:
    testing1 = Signal(name='testing1', value=10, setpoint=2,
                      separate_readback=True)
    logger.info('Python signal: %s' % testing1)


if __name__ == '__main__':
    test()
