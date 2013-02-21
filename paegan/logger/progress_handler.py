from datetime import datetime
import pytz

from collections import deque
import logging

class ProgressHandler(logging.Handler):
    def __init__(self, progress_deque):
        logging.Handler.__init__(self)
        self._progress_deque = progress_deque

    def send(self, s):
        self._progress_deque.append(s)

    def emit(self, record):
        try:
            s = self._format_record(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

    def _format_record(self, record):
        # format log into tuple of:
        # (datetime, progress, message)

        dt = datetime.now().replace(tzinfo=pytz.utc)

        if isinstance(record, list):
            record = tuple(record)

        if isinstance(record, tuple):
            return tuple([dt]) + record
        elif isinstance(record, str) or isinstance(record, unicode):
            return (dt, -1, unicode(record))
        elif isinstance(record, float) or isinstance(record, int):
            return (dt, record, None)
        else:
            return (dt, None, None)

    def close(self):
        self._progress_deque.append(StopIteration)
        logging.Handler.close(self)