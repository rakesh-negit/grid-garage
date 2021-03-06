from __future__ import print_function
import contextlib
import functools
import os
import inspect
import logging
from utils import static_vars
from traceback import format_exception
from sys import exc_info


APPDATA_PATH = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "GridGarage")

LOG_FILE = os.path.join(APPDATA_PATH, "gridgarage.log")


def make_tuple(ob):
    """

    Args:
        ob:

    Returns:

    """

    return ob if isinstance(ob, (list, tuple)) else [ob]


@static_vars(logger=None)
def get_logger():
    """

    Returns:

    """

    if not get_logger.logger:
        get_logger.logger = logging.getLogger("gridgarage")

    return get_logger.logger


def debug(message):
    """

    Args:
        message:

    Returns:

    """

    message = make_tuple(message)

    try:
        logger = get_logger()
        debug_func = logger.debug
    except:
        debug_func = print
        message = ["DEBUG: " + str(msg) for msg in message]

    for msg in message:
        debug_func(msg)

    return


def info(message):
    """

    Args:
        message:

    Returns:

    """

    message = make_tuple(message)

    try:
        logger = get_logger()
        info_func = logger.info
    except:
        info_func = print
        message = ["INFO: " + str(msg) for msg in message]

    for msg in message:
        info_func(msg)

    return


def warn(message):
    """

    Args:
        message:

    Returns:

    """

    message = make_tuple(message)

    try:
        logger = get_logger()
        warn_func = logger.warn
    except:
        warn_func = print
        message = ["WARN: " + str(msg) for msg in message]

    for msg in message:
        warn_func(msg)

    return


def error(message):
    """

    Args:
        message:

    Returns:

    """

    message = make_tuple(message)

    try:
        logger = get_logger()
        error_func = logger.error
    except:
        error_func = print
        message = ["ERROR: " + str(msg) for msg in message]

    for msg in message:
        error_func(msg)

    return


class ArcStreamHandler(logging.StreamHandler):
    """ Logging handler to log messages to ArcGIS """

    def __init__(self, messages):
        """

        Args:
            messages:
        """

        logging.StreamHandler.__init__(self)

        self.messages = messages

    def emit(self, record):
        """ Emit the record to the ArcGIS messages object

        Args:
            record (): The message record

        Returns:

        """

        msg = self.format(record)
        msg = msg.replace("\n", ", ").replace("\t", " ").replace("  ", " ").encode("ascii")
        lvl = record.levelno

        if lvl in [logging.ERROR, logging.CRITICAL]:
            self.messages.addErrorMessage(msg)

        elif lvl == logging.WARNING:
            self.messages.addWarningMessage(msg)

        else:
            self.messages.addMessage(msg)

        self.flush()

        return
