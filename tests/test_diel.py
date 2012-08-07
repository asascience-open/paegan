import unittest
from paegan.transport.location4d import Location4D
from paegan.transport.models.behavior.diel import Diel
from datetime import datetime, timedelta
from paegan.utils.asasuncycles import SunCycles
import pytz

class DielTest(unittest.TestCase):

    #def test_object_from_json(self):
    #    json = 
    #    d = Diel(json=json)

    def test_cycle(self):

        t = datetime.utcnow().replace(tzinfo=pytz.utc)
        loc = Location4D(time=t, latitude=35, longitude=-76)
        c = SunCycles(loc=loc)
        sunrise = c.get_rising()
        sunset = c.get_setting()

        d = Diel()
        d.min_depth = 4
        d.max_depth = 10
        d.pattern = 'cycle'
        d.cycle = 'sunrise'
        d.plus_or_minus = '+'
        d.time_delta = 4
        assert d.get_time(loc4d=loc) == sunrise + timedelta(hours=4)

        d = Diel()
        d.min_depth = 4
        d.max_depth = 10
        d.pattern = 'cycle'
        d.cycle = 'sunset'
        d.plus_or_minus = '-'
        d.time_delta = 2
        assert d.get_time(loc4d=loc) == sunset - timedelta(hours=2)