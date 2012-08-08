import unittest
from paegan.transport.location4d import Location4D
#from paegan.transport.models.behavior.diel import Diel
from datetime import datetime, timedelta

from paegan.utils.asadaylight import Daylight

import pytz
from pytz import timezone

class DaylightTest(unittest.TestCase):

    def test_known(self):

        # Test found here: http://williams.best.vwh.net/sunrise_sunset_example.htm
        lat = 40.9
        lon = -74.3

        dt = datetime(1990, 6, 25, 12, tzinfo=pytz.utc)
        loc = Location4D(time=dt, latitude=lat, longitude=lon)
        d = Daylight(loc=loc)

        zrise = d.get_rise()
        #print "Rise UTC: %s" % zrise
        #print "Rise Eastern: %s" % zrise.astimezone(timezone('US/Eastern'))

        zset = d.get_set()
        #print "Set UTC: %s" % zset
        #print "Set Eastern: %s" % zset.astimezone(timezone('US/Eastern'))
