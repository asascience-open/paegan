import numpy as np
import math
import pylab

class Daylight(object):
    """
      Determines the time of sunrise and sunset for the current julian day.
      Methodology taken from the Almanac for Computers, 1990
        published by Nautical Almanac Office, US Naval Observatory, Wash DC 20392
    """
    zenith = 90.833333 # offical value

    def __init__(self, **kwargs):
        if "loc" not in kwargs:
            if "point" not in kwargs:
                if "lat" not in kwargs or "lon" not in kwargs:
                    raise ValueError("You must supply some form of lat/lon coordinates")
                else:
                    self.lat = kwargs.get("lat")
                    self.lon = kwargs.get("lon")
            else:
                self.lat = kwargs.get("point").y
                self.lon = kwargs.get("point").x
            if "time" not in kwargs:
                raise ValueError("You must supply a datetime object")
            else:
                self.time = kwargs.get("time")   
        else:
            self.lat = kwargs.get("loc").latitude
            self.lon = kwargs.get("loc").longitude
            self.time = kwargs.get("loc").time
        
        self.jd = pylab.date2num(self.time)
        self.longhr = self.lon / 15.
        
    def get_approx_set(self):
        return self.jd + ( (18 - self.longhr) / 24 ) # approx set
    def get_set_hr(self):
        return self.get_set()['hour']
    def get_set_min(self):
        return self.get_set()['minute']
    def get_set(self):
        h, m = self._calc(self.get_approx_set(), 'set')
        if h == -1:
            raise ValueError("Sun will not rise or set at this day at the given point")
        return self.time.replace(hour=int(h)).replace(minute=int(m))
        
    def get_approx_rise(self):
        return self.jd + ( (6 - self.longhr) / 24 ) # approx rise
    def get_rise_hr(self):
        return self.get_rise()['hour']
    def get_rise_min(self):
        return self.get_rise()['minute']
    def get_rise(self):
        h, m = self._calc(self.get_approx_rise(), 'rise')
        if h == -1:
            raise ValueError("Sun will not rise or set at this day at the given point")
        return self.time.replace(hour=int(h)).replace(minute=int(m))
        
    def _calc(self, apx, stage):
        sun_mean_anom = ( 0.9856 * apx ) - 3.289 # sun's mean anomaly
        #sun's longitude
        sun_lon = sun_mean_anom + (1.916 * np.sin(np.degrees( sun_mean_anom ))) \
                + (0.02 * np.sin(np.degrees( 2 * sun_mean_anom ))) + 282.634
        
        if sun_lon > 360:
            sun_lon = sun_lon - 360
        elif sun_lon < 0:
            sun_lon = sun_lon + 360
            
        right_ascension = np.arctan(np.degrees( 0.91764 * np.tan(np.degrees( sun_lon )) )) # sun's right ascension
        
        if right_ascension > 360:
            right_ascension = right_ascension - 360
        elif right_ascension < 0:
            right_ascension = right_ascension + 360  
            
        # put sun's right ascension value in the same quadrant as the sun's
        # true longitude
        lQuad = 90. * np.floor(sun_lon / 90.)
        raQuad = 90. * np.floor(right_ascension / 90.)
        right_ascension = right_ascension + ( lQuad - raQuad)
        right_ascension = right_ascension / 15. # Convert to hours
        
        # Sun's declination
        sinDecl = 0.39782 * np.sin(np.degrees( sun_lon ))
        cosDecl = np.cos( np.arcsin( sinDecl ) )
        
        # Sun's local hour angle
        cosHr = (np.cos(np.degrees( self.zenith )) - ( sinDecl * np.sin(np.degrees(self.lat)) )) \
                * ( cosDecl * np.cos(np.degrees( self.lat )) )

        if cosHr > 1: # Sun doesnt rise on this loc on this date
            return -1, -1
        elif cosHr < -1: # Sun doesnt set on this location on this date
            return -1, -1
        elif stage == 'rise': # Sunrise
            hr = 360 - np.degrees(np.arccos(cosHr))
        elif stage == 'set':  # Sunset
            hr = np.degrees(np.arccos(cosHr))

        print "angle (degrees): %s" % hr
            
        hr = hr / 15. # Convert angle to hours

        print "hours: %s" % hr

        localTime = hr + right_ascension - ( 0.06571 * apx ) # local meantime of rise/set

        print "localtime: %s" % localTime

        UTtime = localTime - self.longhr # adjust to UTC

        if UTtime < 0:
            UTtime = UTtime + 24
        elif UTtime > 24:
            UTtime = UTtime - 24

        print "utc: %s" % UTtime

        hour = np.floor(UTtime)

        minute = (UTtime - hour) * 60
        if minute == 60:
            hour = hour + 1
            minute = 0

        return hour, minute
