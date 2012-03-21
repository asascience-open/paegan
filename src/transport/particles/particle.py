class Particle(object):
	"""
		A particle
	"""
	def __init__(self):
		self._locations = []
	def set_next_location(self, loc):
		self._locations.append(loc)
	def get_locations(self):
		return self._locations
	def get_current_location(self):
		return self._locations[-1]