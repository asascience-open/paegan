import random

class AsaRandom(object):

	@staticmethod
	def random():
	    """
	    pseudo random number generator
	    """
	    rand = random.random()
	    flip = random.random()
	    if flip > 0.5:
	        rand *= -1
	    return rand