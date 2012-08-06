import unittest
from paegan.transport.location4d import Location4D
from paegan.transport.models.behavior.diel import Diel
from datetime import datetime, timedelta

from paegan.utils.asadaylight import Daylight

import pytz
from pytz import timezone

class DaylightTest(unittest.TestCase):

    def test_known(self):

        # Middle of Rhode Island
        lat = 41.7
        lon = -71.7

        # August 6th, 2012 in Rhode Island:
        # Sunrise ~= 5:46 AM 
        # Sunset  ~= 7:58 PM
        dt = datetime(2012, 8, 6, 12, tzinfo=pytz.utc)
        loc = Location4D(time=dt, latitude=lat, longitude=lon)
        d = Daylight(loc=loc)

        zrise = d.get_ephem_rise().astimezone(timezone('US/Eastern'))
        assert zrise.hour == 5
        assert zrise.minute == 46

        zset = d.get_ephem_set().astimezone(timezone('US/Eastern'))
        assert zset.hour == 19
        assert zset.minute == 58

        zrise = d.get_rise()
        #print "Rise UTC: %s" % zrise
        #print "Rise Eastern: %s" % zrise.astimezone(timezone('US/Eastern'))

        zset = d.get_set()
        #print "Set UTC: %s" % zset
        #print "Set Eastern: %s" % zset.astimezone(timezone('US/Eastern'))
