import logging
import collections
import multiprocessing
import threading

from paegan.logger.multi_process_logging import MultiProcessingLogHandler
from paegan.logger.progress_handler import ProgressHandler

class EasyLogger(object):
    def __init__(self, logpath, level=None):

        if level is None:
            level = logging.PROGRESS

        self.logpath = logpath
        self.logger = multiprocessing.get_logger()

        self.queue = multiprocessing.Queue(-1)

        # Close any existing handlers
        self.close_handlers()

        # Remove any existing handlers
        self.logger.handlers = []
        self.logger.setLevel(level)

        handler = MultiProcessingLogHandler(logpath, self.queue)
        handler.setLevel(level)
        formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(processName)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        progress_deque = collections.deque(maxlen=1)
        progress_handler = ProgressHandler(progress_deque)
        progress_handler.setLevel(level)
        self.logger.addHandler(progress_handler)
        self.e = threading.Event()

        def save_progress():
            while self.e.wait(5) != True:
                try:
                    record = progress_deque.pop()
                    if record == StopIteration:
                        break

                    print record

                except Exception:
                    pass
            return

        t = threading.Thread(name="ProgressUpdater", target=save_progress)
        t.daemon = True
        t.start()

    def close_handlers(self):
        (hand.close() for hand in self.logger.handlers)

    def close_queue(self):
        self.queue.put_nowait(StopIteration)
        self.e.set()

    def close(self):
        self.close_handlers()
        self.close_queue()

    def __str__(self):
        return "Logging with MultiProcessingLogHandler in " + self.logpath
