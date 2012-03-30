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

    def set_locations(self, locations):
        self._locations = locations
    def get_locations(self):
        return self._locations
    locations = property(get_locations, set_locations)

    def linestring(self):
        return LineString(map(lambda x: list(x.point.coords)[0], self.locations))