import unittest
from paegan.transport.location4d import Location4D
from datetime import datetime
from paegan.utils.asasuncycles import SunCycles
import pytz
from pytz import timezone

class SunCycleTest(unittest.TestCase):

    def setUp(self):
        # Middle of Rhode Island
        self.lat = 41.7
        self.lon = -71.7

        # August 6th, 2012 in Rhode Island:
        # Sunrise ~= 5:46 AM 
        # Sunset  ~= 7:57 PM
        self.dt = datetime(2012, 8, 6, tzinfo=pytz.utc)

    def test_classmethod_with_location4d(self):

        loc = Location4D(time=self.dt, latitude=self.lat, longitude=self.lon)
        d = SunCycles.cycles(loc=loc)

        zrise = d[SunCycles.RISING].astimezone(timezone('US/Eastern'))
        assert zrise.year == 2012
        assert zrise.month == 8
        assert zrise.day == 6
        assert zrise.hour == 5
        assert zrise.minute == 46

        zset = d[SunCycles.SETTING].astimezone(timezone('US/Eastern'))
        assert zset.year == 2012
        assert zset.month == 8
        assert zset.day == 6
        assert zset.hour == 19
        assert zset.minute == 57

    def test_classmethod_with_lat_lon_time(self):

        d = SunCycles.cycles(lat=self.lat, lon=self.lon, time=self.dt)

        zrise = d[SunCycles.RISING].astimezone(timezone('US/Eastern'))
        assert zrise.year == 2012
        assert zrise.month == 8
        assert zrise.day == 6
        assert zrise.hour == 5
        assert zrise.minute == 46

        zset = d[SunCycles.SETTING].astimezone(timezone('US/Eastern'))
        assert zset.year == 2012
        assert zset.month == 8
        assert zset.day == 6
        assert zset.hour == 19
        assert zset.minute == 57

    def test_alaskan_waters(self):

        d = SunCycles.cycles(lat=59.671120, lon=-144.849561, time=datetime(2011, 5, 2, tzinfo=pytz.utc))

        zrise = d[SunCycles.RISING].astimezone(timezone('US/Alaska'))
        assert zrise.year == 2011
        assert zrise.month == 5
        assert zrise.day == 2
        assert zrise.hour == 5
        assert zrise.minute == 36

        zset = d[SunCycles.SETTING].astimezone(timezone('US/Alaska'))
        assert zset.year == 2011
        assert zset.month == 5
        assert zset.day == 2
        assert zset.hour == 21
        assert zset.minute == 37