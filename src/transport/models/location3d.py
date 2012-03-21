class Location3D:
	"""
		A linestring of particle parameters
	"""
	def __init__(self):
		self._latitude = []
		self._longitude = []
		self._depth = []
		self._velocity = []
		self._temperature = []
		self._salinity = []

	def set_latitude(self, lat):
		self._locations.append(lat)
	def set_longitude(self, lon):
		self._locations.append(lon)
	def set_depth(self, dep):
		self._depth.append(dep)
	def set_velocity(self, vel):
		self._velocity.append(vel)
	def set_temperature(self, tem):
		self._velocity.append(tem)
	def set_salinity(self, sal):
		self._velocity.append(sal)

	def get_latitude(self):
		return self._latitude
	def get_longitude(self):
		return self._longitude
	def get_depths(self):
		return self._depth
	def get_velocity(self):
		return self._velocity
	def get_temperature(self):
		return self._temperature
	def get_salinity(self):
		return self._salinity