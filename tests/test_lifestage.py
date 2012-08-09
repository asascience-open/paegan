import unittest
from paegan.transport.models.behaviors.lifestage import LifeStage
import os
import json
from datetime import datetime
import pytz
from paegan.transport.location4d import Location4D

class LifeStageTest(unittest.TestCase):

    def test_from_json(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/lifestage_single.json"))).read()
        l = LifeStage(json=data)

        assert l.name == 'third'
        assert l.duration == 3
        assert l.linear_a == None
        assert l.linear_b == None
        assert len(l.taxis) == 2
        assert l.taxis[0].min_value == 30.0
        assert l.taxis[0].max_value == 40.0        
        assert len(l.diel) == 2
        assert l.diel[0].min_depth == 2.0
        assert l.diel[0].max_depth == 4.0
        assert l.capability.vss == 5.0
        assert l.capability.variance == 2.0
        assert l.capability.non_swim_turning == 'random'
        assert l.capability.swim_turning == 'random'

        t = datetime.utcnow().replace(tzinfo=pytz.utc)
        loc = Location4D(time=t, latitude=35, longitude=-76)
        assert isinstance(l.diel[0].get_time(loc4d=loc), datetime)

    def test_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/lifestage_single.json"))).read()
        l = LifeStage(data=json.loads(data))

        assert l.name == 'third'
        assert l.duration == 3
        assert l.linear_a == None
        assert l.linear_b == None
        assert len(l.taxis) == 2
        assert l.taxis[1].min_value == 30.0
        assert l.taxis[1].max_value == 50.0        
        assert len(l.diel) == 2
        assert l.diel[1].min_depth == 2.0
        assert l.diel[1].max_depth == 5.0
        assert l.capability.vss == 5.0
        assert l.capability.variance == 2.0
        assert l.capability.non_swim_turning == 'random'
        assert l.capability.swim_turning == 'random'

        t = datetime.utcnow().replace(tzinfo=pytz.utc)
        loc = Location4D(time=t, latitude=35, longitude=-76)
        assert isinstance(l.diel[0].get_time(loc4d=loc), datetime)