import unittest
from paegan.transport.models.behaviors.lifestage import LifeStage
from paegan.transport.models.behavior import LarvaBehavior
import os
import json

class LarvaBehaviorTest(unittest.TestCase):

    def test_from_json(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/behavior_full.json"))).read()
        l = LarvaBehavior(json=data)
        # This is one more because internally we add the DeadLifeStage
        assert len(l.lifestages) == 4

    def test_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/behavior_full.json"))).read()
        l = LarvaBehavior(data=json.loads(data))
        # This is one more because internally we add the DeadLifeStage
        assert len(l.lifestages) == 4