import logging
import multiprocessing
from paegan.logger.multi_process_logging import MultiProcessingLogHandler

class EasyLogger(object):
    def __init__(self, logpath, level=None):

        if level is None:
            level = logging.INFO

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
        # Add handler
        self.logger.addHandler(handler)
        
    def close_handlers(self):
        (hand.close() for hand in self.logger.handlers)
        
    def close_queue(self):
        self.queue.put_nowait(StopIteration)

    def close(self):
        self.close_handlers()
        self.close_queue()

    def __str__(self):
        return "Logging with MultiProcessingLogHandler in " + self.logpath
        