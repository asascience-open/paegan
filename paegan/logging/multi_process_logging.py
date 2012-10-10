from logging import FileHandler
import multiprocessing, threading, logging, sys, traceback
import Queue

class MultiProcessingLogHandler(logging.Handler):
    def __init__(self, name):
        logging.Handler.__init__(self)

        self._handler = FileHandler(name)
        self._done = False
        self.queue = multiprocessing.Queue(-1)

        t = threading.Thread(target=self.receive)
        t.daemon = True
        t.start()

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self._handler.setFormatter(fmt)

    def receive(self):
        while True and not self._done:
            try:
                record = self.queue.get()
                self._handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except IOError:
                traceback.print_exc(file=sys.stderr)
                break
            except:
                traceback.print_exc(file=sys.stderr)
                break

        # Clear the queue
        while True:
            try:
                record = self.queue.get(False)
                self._handler.emit(record)
            except Queue.Empty:
                break
            except:
                traceback.print_exc(file=sys.stderr)
                break

        self.queue.close()
        self._handler.close()
        logging.Handler.close(self)
        return

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
        # Stop the thread loop and close queue
        self._done = True
        # Send the final message to the queue so it loops again
        self.emit("Closing Queue")
        
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
        
        
