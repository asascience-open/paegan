import unittest
from paegan.transport.models.behaviors.lifestage import LifeStage
from paegan.transport.models.behavior import LarvaBehavior
import os
import json

class LarvaBehaviorTest(unittest.TestCase):

    def test_from_json(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/behavior_full.json"))).read()
        l = LarvaBehavior(json=data)
        assert len(l.lifestages) == 3

    def test_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/behavior_full.json"))).read()
        l = LarvaBehavior(data=json.loads(data))
        assert len(l.lifestages) == 3