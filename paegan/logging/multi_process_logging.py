from logging import FileHandler
import multiprocessing, threading, logging, sys, traceback

class MultiProcessingLogHandler(logging.Handler):
    def __init__(self, name):
        logging.Handler.__init__(self)

        self._handler = FileHandler(name)
        self.queue = multiprocessing.Queue(-1)

        t = threading.Thread(target=self.receive)
        t.daemon = True
        t.start()

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self._handler.setFormatter(fmt)

    def receive(self):
        while True:
            try:
                record = self.queue.get()
                self._handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                traceback.print_exc(file=sys.stderr)

    def send(self, s):
        self.queue.put_nowait(s)

    def _format_record(self, record):
        # ensure that exc_info and args
        # have been stringified.  Removes any chance of
        # unpickleable things inside and possibly reduces
        # message size sent over the pipe
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            dummy = self.format(record)
            record.exc_info = None

        return record

    def emit(self, record):
        try:
            s = self._format_record(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        self._handler.close()
        logging.Handler.close(self)
        
class EasyLogger(object):
    def __init__(self, logpath):
        self.logpath = logpath
        self.logger = multiprocessing.get_logger()

        # Close any existing handlers
        self.close()
        # Remove any existing handlers
        self.logger.handlers = []

        self.logger.setLevel(logging.INFO)
        handler = MultiProcessingLogHandler(logpath)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(name)s - %(processName)s - %(message)s')
        handler.setFormatter(formatter)
        # Add handler
        self.logger.addHandler(handler)
        
    def close(self):
        (hand.close() for hand in self.logger.handlers)

    def __str__(self):
        return "Logging with MultiProcessingLogHandler in " + self.logpath
        
        
