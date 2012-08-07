import numpy as np
import ephem
import pytz

class SunCycles(object):

    def __init__(self, **kwargs):
        """
        Parameters:
            loc = Location4D (object)
                OR
            point = Shapely point (object)
            time = datetime (object)
                OR
            lat = latitude (float)
            lon = longitude (float)
            time = datetime (object)
        """
        if "loc" not in kwargs:
            if "point" not in kwargs:
                if "lat" not in kwargs or "lon" not in kwargs:
                    raise ValueError("You must supply some form of lat/lon coordinates")
                else:
                    lat = kwargs.get("lat")
                    lon = kwargs.get("lon")
            else:
                lat = kwargs.get("point").y
                lon = kwargs.get("point").x
            if "time" not in kwargs:
                raise ValueError("You must supply a datetime object")
            else:
                time = kwargs.get("time")   
        else:
            lat = kwargs.get("loc").latitude
            lon = kwargs.get("loc").longitude
            time = kwargs.get("loc").time

        self._sun = ephem.Sun()
        self._loc = ephem.Observer()
        self._loc.lon = "%s" % lon
        self._loc.lat = "%s" % lat
        self._loc.date = "%s/%s/%s 00:00" % (time.year, time.month, time.day)

    def get_rising(self, **kwargs):
        """
        Return the next sun rising as a UTC datetime
        """
        return self._loc.next_rising(self._sun).datetime().replace(tzinfo=pytz.utc)

    def get_setting(self):
        """
        Return the next sun setting as a UTC datetime
        """
        return self._loc.next_setting(self._sun).datetime().replace(tzinfo=pytz.utc)

    @classmethod
    def cycles(cls, **kwargs):
        """
        Classmethod for convienence in returning both the sunrise and sunset
        based on a location and date.  Always calculates the sunrise and sunset on the
        given date, no matter the time passed into the function in the datetime object.

        Parameters:
            loc = Location4D (object)
                OR
            point = Shapely point (object)
            time = datetime in UTC (object)
                OR
            lat = latitude (float)
            lon = longitude (float)
            time = datetime in UTC (object)

        Returns:
            { 'rising': datetime in UTC, 'setting': datetime in UTC }
        """
        if "loc" not in kwargs:
            if "point" not in kwargs:
                if "lat" not in kwargs or "lon" not in kwargs:
                    raise ValueError("You must supply some form of lat/lon coordinates")
                else:
                    lat = kwargs.get("lat")
                    lon = kwargs.get("lon")
            else:
                lat = kwargs.get("point").y
                lon = kwargs.get("point").x
            if "time" not in kwargs:
                raise ValueError("You must supply a datetime object")
            else:
                time = kwargs.get("time")   
        else:
            lat = kwargs.get("loc").latitude
            lon = kwargs.get("loc").longitude
            time = kwargs.get("loc").time

        sun = ephem.Sun()
        loc = ephem.Observer()
        loc.lon = "%s" % lon
        loc.lat = "%s" % lat
        loc.date = "%s/%s/%s 00:00" % (time.year, time.month, time.day)

        return { 'rising' : loc.next_rising(sun).datetime().replace(tzinfo=pytz.utc),
                 'setting': loc.next_setting(sun).datetime().replace(tzinfo=pytz.utc) }