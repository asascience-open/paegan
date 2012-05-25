from shapely.geometry import LineString

class Particle(object):
    """
        A particle
    """
    def __init__(self):
        self._locations = []

    def set_location(self, location):
        self._locations.append(location)
    def get_location(self):
        return self._locations[-1]
    location = property(get_location, set_location)

    def get_locations(self):
        return self._locations
    locations = property(get_locations, None)

    def set_active(self, active):
        self._active = active
    def get_active(self):
        return self._active
    active = property(get_active, set_active)

    def get_last_movement(self):
        return LineString(list(self.locations[-2].point.coords) + list(self.locations[-1].point.coords))

    def linestring(self):
        return LineString(map(lambda x: list(x.point.coords)[0], self.locations))