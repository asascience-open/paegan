import multiprocessing
from paegan.logger.null_handler import NullHandler

logger = multiprocessing.get_logger()
logger.addHandler(NullHandler())