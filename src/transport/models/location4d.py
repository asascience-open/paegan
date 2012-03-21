class Location4D(object):
    """
        A point in space, with envronmental parameters
    """

    def __init__(self, lat, lon, depth=None):
        self._latitude = lat
        self._longitude = lon
        self._depth = depth

    def set_latitude(self, lat):
        self._latitude = lat
    def get_latitude(self):
        return self._latitude
    latitude = property(get_latitude, set_latitude)

    def set_longitude(self, lon):
        self._longitude = lon
    def get_longitude(self):
        return self._longitude
    longitude = property(get_longitude, set_longitude)

    def set_depth(self, dep):
        self._depth = dep
    def get_depth(self):
        return self._depth
    depth = property(get_depth, set_depth)

    def set_u(self, u):
        self._u = u
    def get_u(self):
        return self._u
    u = property(get_u, set_u)

    def set_v(self, v):
        self._v = v
    def get_v(self):
        return self._v
    v = property(get_v, set_v)

    def set_z(self, z):
        self._z = z
    def get_z(self):
        return self._z
    z = property(get_z, set_z)

    def set_time(self, time):
        self._time = time
    def get_time(self):
        return self._time
    time = property(get_time, set_time)

    def __str__(self):
        return  " *** Location3D *** " + \
                "\nlatitude: " + str(self.latitude) + \
                "\nlongitude: " + str(self.longitude) + \
                "\ndepth: " + str(self.depth) + \
                "\ntime: " + str(self.time)
