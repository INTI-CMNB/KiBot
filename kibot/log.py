# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
"""
Log module

Handles logging initialization and formatting.
"""
import io
import os
import re
import sys
import traceback
import logging
from .misc import WARN_AS_ERROR
no_colorama = False
try:
    from colorama import init as colorama_init, Fore, Back, Style
except ImportError:
    no_colorama = True
# If colorama isn't installed use an ANSI basic replacement
if no_colorama:
    from .mcpyrate.ansi import Fore, Back, Style  # noqa: F811
else:
    colorama_init()
# Default domain, base name for the tool
domain = 'kilog'
filters = []
root_logger = None
visual_level = None
debug_level = 0
stop_on_warnings = False
dont_stop = False
errors_ignored = False
record_error_msgs = False
recorded_error_msgs = []
re_dk_client_id = re.compile("DIGIKEY_CLIENT_ID=([^']+)")
re_dk_client_secret = re.compile("DIGIKEY_CLIENT_SECRET=([^']+)")


def get_logger(name=None, indent=None):
    """Get a module for a submodule or the root logger if no name is
       provided"""
    # print('get_logger '+str(name))
    global root_logger
    if root_logger is None:
        init()
    if name:
        if name.startswith(domain):
            lg = logging.getLogger(name)
        else:
            lg = logging.getLogger(domain+'.'+name)
    else:
        lg = logging.getLogger(domain)
    lg.indent = indent
    return lg


def set_domain(name):
    """Set the base name for the tool"""
    global domain
    domain = name


def set_filters(f):
    """Set the list of warning filters"""
    if f:
        global filters
        filters = f+filters


def start_recording_error_msgs():
    recorded_error_msgs.append([])


def stop_recording_error_msgs(joined=True):
    return '\n'.join(recorded_error_msgs.pop()) if joined else recorded_error_msgs.pop()


def push_error_msg(msg):
    if not len(recorded_error_msgs):
        return
    recorded_error_msgs[-1].append(msg)


class MyLogger(logging.Logger):
    warn_hash = {}
    warn_tcnt = warn_cnt = n_filtered = 0

    @staticmethod
    def reset_warn_hash():
        """ Clean the hash, used for testing """
        MyLogger.warn_hash = {}

    def warning(self, msg, *args, **kwargs):
        MyLogger.warn_tcnt += 1
        # Get the message applying optional C style expansions
        # No longer used:
        # if isinstance(msg, str) and len(args):
        #     buf = StringIO()
        #     buf.write(msg % args)
        #     buf = buf.getvalue()
        # else:
        buf = str(msg)
        # Avoid repeated warnings
        if buf in MyLogger.warn_hash:
            MyLogger.warn_hash[buf] += 1
            return
        # Apply the filters
        if filters and buf.startswith('(W'):
            pos_end = buf.find(')')
            if pos_end > 0:
                num_str = buf[2:pos_end]
                id = buf[1:pos_end]
                if num_str[0] == 'C':
                    number = int(buf[3:pos_end])+1000
                else:
                    number = int(num_str)
                for f in filters:
                    if (f.number == number or f.error == id) and f._regex.search(buf):
                        MyLogger.n_filtered += 1
                        self.debug('Filtered warning: '+buf, **kwargs)
                        return
        MyLogger.warn_cnt += 1
        MyLogger.warn_hash[buf] = 1
        if sys.version_info >= (3, 8):
            super().warning(buf, stacklevel=2, **kwargs)  # pragma: no cover (Py38)
        else:
            super().warning(buf, **kwargs)
        self.check_warn_stop()

    def error(self, msg, *args, **kwargs):
        buf = str(msg)
        push_error_msg(buf)
        if sys.version_info >= (3, 8):
            super().error(buf, stacklevel=2, **kwargs)  # pragma: no cover (Py38)
        else:
            super().error(buf, **kwargs)

    def check_warn_stop(self):
        if stop_on_warnings:
            self.error('Warnings treated as errors')
            if dont_stop:
                pass
            else:
                sys.exit(WARN_AS_ERROR)

    def log(self, level, msg, *args, **kwargs):
        if level < self.getEffectiveLevel():
            return
        if isinstance(msg, tuple):
            msg = ' '.join(map(str, msg))
        if sys.version_info >= (3, 8):
            super(self.__class__, self).debug(msg, *args, **kwargs, stacklevel=2)  # pragma: no cover (Py38)
        else:
            super(self.__class__, self).debug(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        # Avoid leaking secrets in the log files
        # Digi-Key KiCost plug-in variables
        if 'DIGIKEY_' in str(msg):
            match = re_dk_client_id.search(msg)
            if match:
                val = match.group(1)
                new_val = 'x'*(len(val)-3)+val[-3:]
                msg = msg.replace(val, new_val)
            match = re_dk_client_secret.search(msg)
            if match:
                val = match.group(1)
                new_val = 'x'*(len(val)-3)+val[-3:]
                msg = msg.replace(val, new_val)
        if sys.version_info >= (3, 8):
            super(self.__class__, self).debug(msg, *args, **kwargs, stacklevel=2)  # pragma: no cover (Py38)
        else:
            super(self.__class__, self).debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if isinstance(msg, tuple):
            msg = ' '.join(map(str, msg))
        if self.indent:
            msg = ' '*self.indent+msg
        super(self.__class__, self).info(msg, *args, **kwargs)

    def debugl(self, level, msg, *args, **kwargs):
        # Similar to log() but using the debug_level (-vvvv) instead of the Python level
        global debug_level
        if level > debug_level:
            return
        if isinstance(msg, tuple):
            msg = ' '.join(map(str, msg))
        if sys.version_info >= (3, 8):
            super(self.__class__, self).debug(msg, *args, **kwargs, stacklevel=2)  # pragma: no cover (Py38)
        else:
            super(self.__class__, self).debug(msg, *args, **kwargs)

    def log_totals(self):
        if MyLogger.warn_cnt or MyLogger.warn_tcnt:
            filt_msg = ''
            if MyLogger.n_filtered:
                filt_msg = ', {} filtered'.format(MyLogger.n_filtered)
            self.info('Found {} unique warning/s ({} total{})'.format(MyLogger.warn_cnt, MyLogger.warn_tcnt, filt_msg))

    def non_critical_error(self, msg, *args, **kwargs):
        buf = str(msg)
        push_error_msg(buf)
        if sys.version_info >= (3, 8):
            super().error(buf, stacklevel=2, **kwargs)  # pragma: no cover (Py38)
        else:
            super().error(buf, **kwargs)
        self.check_warn_stop()

    def findCaller(self, stack_info=False, stacklevel=1):
        f = sys._getframe(1)
        # Skip frames from logging module
        while '/logging/' in os.path.normcase(f.f_code.co_filename):
            f = f.f_back
        # Apply the indicated stacklevel
        while stacklevel > 1:
            f = f.f_back
            stacklevel -= 1
        # Skip the __init__.py wrappers
        fname = os.path.normcase(f.f_code.co_filename)
        if fname.endswith('__init__.py') or fname.endswith('log__.py'):
            f = f.f_back
        # Create the stack info if needed
        sinfo = None
        if stack_info:
            out = io.StringIO()
            out.write(u"Stack (most recent call last):\n")
            traceback.print_stack(f, file=out)
            sinfo = out.getvalue().rstrip(u"\n")
        return os.path.normcase(f.f_code.co_filename), f.f_lineno, f.f_code.co_name, sinfo


def set_verbosity(logger, verbose, quiet):
    # Choose the log level
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG
    if quiet:
        log_level = logging.WARNING
    # We use debug level but we then filter according to the desired level (visual_level)
    # In this way we can log debug to files and only the user level to the console
    logger.setLevel(logging.DEBUG)
    global visual_level
    visual_level = log_level
    return log_level <= logging.DEBUG


class FilterOnlyInfo(object):
    def filter(self, record):
        if visual_level is not None and record.levelno < visual_level:
            return False
        return record.levelno == logging.INFO


class FilterNoInfo(object):
    def filter(self, record):
        if visual_level is not None and record.levelno < visual_level:
            return False
        return record.levelno != logging.INFO


def init():
    """Initialize the logging feature using a custom format"""
    global root_logger
    if root_logger is not None:
        return root_logger
    # Use a class to count and filter warnings
    logging.setLoggerClass(MyLogger)
    # get_logger will call init is the root_logger is None, avoid a loop
    root_logger = True
    root_logger = logger = get_logger()
    # Handler for all but info.
    # Outputs to stderr
    ch = logging.StreamHandler()
    ch.addFilter(FilterNoInfo())
    ch.setFormatter(CustomFormatter(sys.stderr))
    logger.addHandler(ch)
    # Handler for info.
    # Outputs to stdout
    ch = logging.StreamHandler(sys.stdout)
    ch.addFilter(FilterOnlyInfo())
    ch.setFormatter(CustomFormatter(sys.stdout))
    logger.addHandler(ch)
    return logger


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors"""

    def __init__(self, stream=None, force_tty=False):
        super(logging.Formatter, self).__init__()
        if (stream is not None and stream.isatty()):
            white = Fore.WHITE
            yellow = Fore.YELLOW + Style.BRIGHT
            red = Fore.RED + Style.BRIGHT
            red_alarm = Fore.RED + Back.WHITE + Style.BRIGHT
            cyan = Fore.CYAN + Style.BRIGHT
            reset = Style.RESET_ALL
        elif force_tty:
            # This mechanism is used by the GUI, is simpler than parsing ANSI escape sequences
            white = ""
            yellow = "\033Y"
            red = "\033R"
            red_alarm = "\033r"
            cyan = "\033C"
            reset = ""
        else:
            white = ""
            yellow = ""
            red = ""
            red_alarm = ""
            cyan = ""
            reset = ""
        # format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
        #          "(%(filename)s:%(lineno)d)"
        format = "%(levelname)s:%(message)s (%(name)s - %(filename)s:%(lineno)d)"
        format_simple = "%(message)s"

        self.FORMATS = {
            logging.DEBUG: cyan + format + reset,
            logging.INFO: white + format_simple + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: red_alarm + format + reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def set_file_log(fname):
    fh = logging.FileHandler(fname)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(CustomFormatter())
    root_logger.addHandler(fh)
    return fh


def remove_file_log(fh):
    root_logger.removeHandler(fh)


def set_log_handler(handler):
    global visual_level
    handler.setLevel(visual_level)
    handler.setFormatter(CustomFormatter(force_tty=True))
    root_logger.addHandler(handler)
    return handler


def remove_log_handler(handler):
    root_logger.removeHandler(handler)
