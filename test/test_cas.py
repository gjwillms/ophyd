from __future__ import print_function

import unittest
import logging
import time

import numpy as np
from numpy.testing import assert_array_equal

import epics

from ophyd.controls.cas import (CasPV, CasRecord, Limits, casAsyncCompletion)
from ophyd.utils.errors import alarms
from ophyd.utils.epics_pvs import record_field
from ophyd.session import get_session_manager
from . import get_caserver

server = None
logger = logging.getLogger(__name__)
session = get_session_manager()


def setUpModule():
    global server

    server = get_caserver()
    server._pv_idx = 0


def tearDownModule():
    pass


def caget(pvc, **kwargs):
    get_value = pvc.get(with_ctrlvars=True, use_monitor=False, **kwargs)
    logger.debug('[%f] %s %s (severity=%d)' %
                 (pvc.timestamp, get_value, alarms.get_name(pvc.status), pvc.severity)
                 )
    return get_value


def client_pv(pvname):
    pvc = epics.PV(pvname, form='time')
    pvc.wait_for_connection()
    if not pvc.connected:
        raise Exception('Failed to connect to pv %s' % pvname)

    return pvc


def get_pvname():
    server._pv_idx += 1
    return '%s__cas_test_pv_%d' % (server.prefix, server._pv_idx)


class CASTests(unittest.TestCase):
    def test_float(self, pv_name='testing'):
        pv_name = get_pvname()
        limits = Limits(lolo=0.1, low=0.2, high=0.4, hihi=0.5)

        # pvs = server, pvc = client
        pvs = CasPV(pv_name, 0.0, limits=limits,
                    units='test', server=server)
        pvc = client_pv(pv_name)

        logger.info('client put, client get')
        for i in range(6):
            value = 0.1 * i
            pvc.put(0.1 * i)
            self.assertEquals(caget(pvc), value)

        logger.info('server put, client get')
        for i in range(6):
            value = 0.1 * i
            pvs.value = value
            self.assertEquals(caget(pvc), value)

        server.remove_pv(pvs)

    def test_string(self):
        pv_name = get_pvname()
        pvs = CasPV(pv_name, 'test', units='test')
        server.add_pv(pvs)

        pvc = client_pv(pv_name)

        logger.info(pvc.info)
        value = '"string pv"'
        pvc.put(value)

        get_value = pvc.get(use_monitor=False)
        logger.info('string pv: %s' % get_value)
        self.assertEquals(value, get_value)

        server.remove_pv(pvs.name)

    def test_start_twice(self):
        server.start()
        server.running

    def test_enum(self):
        pv_name = get_pvname()
        pvs = CasPV(pv_name, ['a', 'b', 'c'], units='test',
                    minor_states=['a'],
                    major_states=['c'])

        server.add_pv(pvs)
        pvc = client_pv(pv_name)

        self.assertEquals(caget(pvc, as_string=True), 'a')
        pvc.put('b')
        self.assertEquals(caget(pvc, as_string=True), 'b')
        pvc.put('c')
        self.assertEquals(caget(pvc, as_string=True), 'c')

    def test_async(self):
        def written_to(**kwargs):
            logger.debug('written_to-> %s' % kwargs)

        pv_name = get_pvname()
        pvs = CasPV(pv_name, 0.0, server=server,
                    written_cb=written_to)
        pvc = client_pv(pv_name)

        caget(pvc)
        pvc.put(10.0)
        caget(pvc)

        def written_to_async(timestamp=None, value=None,
                             status=None, severity=None,
                             pv=None, **kwargs):
            raise casAsyncCompletion

        def finished(**kwargs):
            logger.debug('caput completed', kwargs)

        pvs._written_cb = written_to_async
        pvc.put(12, wait=False, use_complete=True, callback=finished)
        time.sleep(0.05)
        # Indicate completion to client
        pvs.async_done()

        caget(pvc)

    def test_numpy(self):
        pv_name = get_pvname()
        arr = np.arange(10)
        pvs = CasPV(pv_name, arr, server=server)
        pvc = client_pv(pv_name)

        pvs[1:4] = 4
        result = [0, 4, 4, 4, 4, 5, 6, 7, 8, 9]
        assert_array_equal(caget(pvc), result)
        assert_array_equal(pvs[1:4], [4, 4, 4])

        if 0:
            # TODO pyepics doesn't play well with resizing
            pvc.disconnect()
            pvc.connect()

            pvs.resize(20)
            pvs[10:] = result
            pvc._args['count'] = 20
            assert_array_equal(caget(pvc), result * 2)

    def test_record(self):
        record = get_pvname()
        val_field = record_field(record, 'VAL')
        egu_field = record_field(record, 'EGU')

        arr = np.arange(10)
        pvs = CasRecord(record, arr)
        pvs.add_field('EGU', 'testing')

        server.add_pv(pvs)

        record_pvc = client_pv(record)
        field_pvc = client_pv(val_field)
        egu_pvc = client_pv(egu_field)

        value = [1] * 10
        record_pvc.put(value)

        assert_array_equal(caget(record_pvc), value)
        assert_array_equal(caget(record_pvc), caget(field_pvc))
        self.assertEquals(caget(egu_pvc), 'testing')


from . import main
is_main = (__name__ == '__main__')
main(is_main)
