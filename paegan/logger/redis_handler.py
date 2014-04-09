import time
import json
import logging
from datetime import datetime

import pytz

try:
    import redis
except ImportError:
    pass


class RedisHandler(logging.Handler):
    """
    Publish messages to redis channel.
    """

    def __init__(self, channel, redis_url):
        """
        Create a new logger for the given channel and redis_url
        """
        logging.Handler.__init__(self)
        self.channel = channel
        self.redis_client = redis.from_url(redis_url)

    def emit(self, record):
        """
        Publish record to redis logging channel
        """
        try:
            self.redis_client.publish(self.channel, self._format_record(record))
        except redis.RedisError:
            pass
        except Exception:
            self.handleError(record)

    def _format_record(self, record):
        # format log into tuple of:
        # (datetime, progress, message)

        # Get a timezone aware datetime from time.time()
        dt = datetime.fromtimestamp(record.created).replace(tzinfo=pytz.timezone(time.strftime("%Z",time.gmtime()))).astimezone(pytz.utc)
        payload = { "time"    : dt.isoformat(),
                    "value"   : None,
                    "message" : None,
                    "level"   : record.levelname }

        msg = record.msg

        """ This allows for things like:

            logger.progress((2, "Initializing particles"))
            logger.info("word to yo momma")
            logger.progress(30)
        """
        if isinstance(msg, list) or isinstance(msg, tuple):
            payload["value"] = msg[0]
            payload["message"] = msg[1]
        elif isinstance(msg, str) or isinstance(msg, unicode):
            payload["message"] = msg
        elif isinstance(msg, float) or isinstance(msg, int):
            payload["value"] = msg
        else:
            payload["message"] = msg

        return json.dumps(payload)

    def close(self):
        self.redis_client.close()
        logging.Handler.close(self)