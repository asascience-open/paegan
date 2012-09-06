from shapely.geometry import Point
from copy import deepcopy

class Location4D(object):
    """
        A point in space and time
    """

    def __init__(self, **kwargs):
        """ Mandatory named arguments:
            * location (Location4d Object)
            OR
            * point (Shapely Point Object)
            OR 
            * latitude (DD)
            * longitude (DD)

            Optional named arguments: 
            * depth (meters)
            * time (DateTime Object)
        """
        if "location" in kwargs:
            loc = kwargs.pop('location')
            self.latitude = deepcopy(loc.latitude)
            self.longitude = deepcopy(loc.longitude)
            self.depth = deepcopy(loc.depth)
            self.time = deepcopy(loc.time)
        elif "point" in kwargs:
            self.point = kwargs.pop('point')
            self.time = kwargs.pop('time', None) 
        elif "latitude" and "longitude" in kwargs:
            self.latitude = kwargs.pop('latitude')
            self.longitude = kwargs.pop('longitude')
            self.depth = kwargs.pop('depth', None)
            self.time = kwargs.pop('time', None) 
        else:
            raise TypeError( "must provide a location4d object, a point geometry object, or a latitude and longitude" )

        self._dirty = True

    def set_point(self, point):
        self._point = point
        self._latitude = point.y
        self._longitude = point.x
        self._depth = point.z
        self._dirty = False
    def get_point(self):
        if self._dirty:
            self.point = Point(self._longitude, self._latitude, self._depth)
        return self._point
    point = property(get_point, set_point)

    def set_latitude(self, lat):
        self._latitude = lat
        self._dirty = True
    def get_latitude(self):
        return self._latitude
    latitude = property(get_latitude, set_latitude)

    def set_longitude(self, lon):
        self._longitude = lon
        self._dirty = True
    def get_longitude(self):
        return self._longitude
    longitude = property(get_longitude, set_longitude)

    def set_depth(self, dep):
        """
            Depth below sea level, positive up
        """
        self._depth = dep
        self._dirty = True
    def get_depth(self):
        return self._depth
    depth = property(get_depth, set_depth)

    def set_time(self, time):
        self._time = time
    def get_time(self):
        return self._time
    time = property(get_time, set_time)

    def __str__(self):
        return  " *** Location4D *** " + \
                "\nlatitude: " + str(self.latitude) + \
                "\nlongitude: " + str(self.longitude) + \
                "\ndepth: " + str(self.depth) + \
                "\ntime: " + str(self.time)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)