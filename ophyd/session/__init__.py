''' '''
from __future__ import print_function
import sys
import logging
import warnings

LOG_FORMAT = "%(asctime)-15s [%(name)5s:%(levelname)s] %(message)s"
OPHYD_LOGGER = 'ophyd_session'


def get_session_manager():
    from .sessionmgr import SessionManager

    if SessionManager._instance is None:
        logger.warning('Instantiating SessionManager outside of IPython')
        SessionManager(logging.getLogger(OPHYD_LOGGER), None)

    return SessionManager._instance


def register_object(obj, notify=True):
    '''Register the object with the current running ophyd session.

    Parameters
    ----------
    obj : object
        The object to register
    notify : bool, optional
        If set, the object will be notified of its registration with the session
        manager.

    Returns
    -------
    session : SessionManager or None
        The current session
    '''
    ses = get_session_manager()
    ses_logger = ses.register(obj)

    if notify:
        obj._registered(ses, ses_logger)

    return ses


def setup_loggers(logger_names, fmt=LOG_FORMAT):
    fmt = logging.Formatter(LOG_FORMAT)
    for name in logger_names:
        logger = logging.getLogger(name)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(fmt)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

# setup logging
setup_loggers((OPHYD_LOGGER, ))
logger = logging.getLogger(OPHYD_LOGGER)


def load_ipython_extension(ipython):
    warnings.simplefilter('default')

    print('Loading Ophyd Session Manager...')

    from .sessionmgr import SessionManager
    # SessionManager will insert itself into ipython user namespace
    session_mgr = SessionManager(logger=logger, ipy=ipython)

    print('...Done loading Ophyd Session Manager')
