import contextlib
import json
import logging
import os
import sys
import warnings
from logging import Formatter


class DefaultOrganize(Formatter):
    def __init__(self, extra):
        """Initialize the log formatter

        Arguments:
            extra -- A dict to be merge with the josn message, update at this dict imediate aplays
        """
        self.extra = extra
        super().__init__()

    def format(self, record):
        data = {
            "datetime": self.formatTime(record),
            "level": record.levelname,
            "msg": record.msg % record.args,
            "log_hierarchy": record.name,
            "function": record.funcName,
            "module": record.module,
            "thread_name": record.threadName,
        }

        data.update(self.extra)

        if record.exc_info:
            data["traceback"] = self.formatException(record.exc_info)

        if record.stack_info:
            data["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(data)


class ExecLogger(logging.getLoggerClass()):
    """A logger class that allows dinamic extra keys when used with
    a formatter thar suport `extra` atribute
    """

    def __init__(self, name):
        self.context = {}
        self._formatter = None
        super().__init__(name)

    @property
    def formatter(self):
        """The Formatter that efectively insert the custom key

        None:
            To have some effect the formatter must suport `extra` attribute
        """

        return self._formatter

    @formatter.setter
    def formatter(self, formatter):
        self._formatter = formatter
        if hasattr(formatter, "extra"):
            formatter.extra.update(self.context)
            self.context = formatter.extra

    def set(self, **kargs):
        """Set a context to the logger

        Keyword Arguments:
            **kargs -- Any know argument is add as a key in the log context
                Pass `None` to remove the key
        """

        self.context.update(kargs)
        for k, value in kargs.items():
            if value is None:
                del self.context[k]

    def reset(self):
        """Clear all the log context"""

        self.context.clear()

    @contextlib.contextmanager
    def extra(self, **kargs):
        """Context Mannager to set and rollback the log context

        Example::
            logger.set(a='before')
            logger.error('fail before context') # log { ... "a": "before" }
            with logger.extra(a='in', b='context'):
                logger.error('fail inside context') # log { ... "a": "in", "b": "context" }
            logger.error('fail after context') # log { ... "a": "after" }

        Decorators:
            contextmanager

        Keyword Arguments:
            **kargs -- Any know argument is add as a key in the log context
                Pass `None` to remove the key
        """

        try:
            old_contex = self.context.copy()
            self.set(**kargs)
            yield self
        finally:
            self.reset()
            self.context.update(old_contex)


def setup(**kargs):
    """
    Note:
       This function MUST be called in the entry point of the program before any log

    Keyword Arguments:
        **kargs -- Any know argument is add as a key in the log
        use this only to fixed keys, prefere `logger.set` or `logger.extra` to mutable keys
        see `ExecLogger` documentation
    """
    name = "default"
    if "name" in kargs:
        name = kargs["name"]

    if issubclass(logging.getLoggerClass(), ExecLogger):
        return

    logging.setLoggerClass(ExecLogger)

    logging_level = os.getenv("LOG_LEVEL", "INFO")

    if not logging_level:
        logging_level = "INFO"

    if logging_level == "TRACE":
        logging_level = "DEBUG"
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)

    logging.getLogger().handlers.clear()

    formatter = DefaultOrganize(extra=kargs)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging_level)

    logging.getLogger(name).formatter = formatter


def setup_logging(**kargs):
    """
    Deprecate:
        Use `logger.set` or `logger.extra` instead

    Note:
        before setup the logger can be get with::

            import logging
            logger = logging.getLogger()

        There are no need to pass around the logger

    Keyword Arguments:
        **kargs -- Any know argument is add as a key in the log

    Returns:
        ExecLogger -- The logger already configured
    """
    logger = getLogger()

    warnings.warn(
        "setup_logging is deprecate, use `logger.set` or `logger.extra` instead", DeprecationWarning, stacklevel=2
    )

    logger.reset()
    logger.set(**kargs)

    return logger


def getLogger(name=None):
    """Get the fx Logger

    Note:
        This is the only safe way to get a logger tha has set and reset available
    Returns:
        ExecLogger -- The logger already configured
    """

    setup(name=None)
    return logging.getLogger(name)
