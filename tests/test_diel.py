import unittest
from paegan.transport.location4d import Location4D
from paegan.transport.models.behaviors.diel import Diel
from datetime import datetime, timedelta
from paegan.utils.asasuncycles import SunCycles
import pytz
import os
import json

class DielTest(unittest.TestCase):

    def test_cycle_object_from_json(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/diel_behavior_cycle.json"))).read()
        d = Diel(json=data)

        assert d.pattern == "cycles"
        assert d.plus_or_minus == "+"
        assert d.min_depth == -4.0
        assert d.max_depth == -5.0
        assert d.time_delta == 4
        assert d.cycle == "sunrise"

    def test_cycle_object_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/diel_behavior_cycle.json"))).read()
        d = Diel(data=json.loads(data))

        assert d.pattern == "cycles"
        assert d.plus_or_minus == "+"
        assert d.min_depth == -4.0
        assert d.max_depth == -5.0
        assert d.time_delta == 4
        assert d.cycle == "sunrise"

    def test_specifictime_object_from_json(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/diel_behavior_specifictime.json"))).read()
        d = Diel(json=data)

        assert d.pattern == "specifictime"
        assert d.min_depth == -4.0
        assert d.max_depth == -5.0
        assert d.time == datetime.utcfromtimestamp(1344272400000 / 1000).replace(tzinfo=pytz.utc)

    def test_specifictime_object_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/diel_behavior_specifictime.json"))).read()
        d = Diel(data=json.loads(data))

        assert d.pattern == "specifictime"
        assert d.min_depth == -4.0
        assert d.max_depth == -5.0
        assert d.time == datetime.utcfromtimestamp(1344272400000 / 1000).replace(tzinfo=pytz.utc)

    def test_cycle(self):

        t = datetime.utcnow().replace(tzinfo=pytz.utc)
        loc = Location4D(time=t, latitude=35, longitude=-76)
        c = SunCycles.cycles(loc=loc)
        sunrise = c[SunCycles.RISING]
        sunset = c[SunCycles.SETTING]

        d = Diel()
        d.min_depth = -4
        d.max_depth = -10
        d.pattern = 'cycles'
        d.cycle = 'sunrise'
        d.plus_or_minus = '+'
        d.time_delta = 4
        assert d.get_time(loc4d=loc) == sunrise + timedelta(hours=4)

        d = Diel()
        d.min_depth = -4
        d.max_depth = -10
        d.pattern = 'cycles'
        d.cycle = 'sunset'
        d.plus_or_minus = '-'
        d.time_delta = 2
        assert d.get_time(loc4d=loc) == sunset - timedelta(hours=2)