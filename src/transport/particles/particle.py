class Particle:
	"""
		A particle
	"""
	def __init__(self):
		self._locations = []
		self._velocity = []
		self._depth = []
	def set_next_location(self, loc):
		self._locations.append(loc)
	def set_next_velocity(self, vel):
		self._velocity.append(vel)
	def set_next_depth(self, dep):
		self._depth.append(dep)
	def get_locations(self):
		return self._locations
	def get_velocities(self):
		return self._velocity
	def get_depths(self):
		return self._depth
	def get_current_location(self):
		return self._locations[-1]
	def get_current_velocity(self):
		return self._velocity[-1]
	def get_current_depth(self):
		return self._depth[-1]