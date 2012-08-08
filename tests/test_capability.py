import unittest
from paegan.transport.models.behavior.capability import Capability
import os
import json

class TaxisTest(unittest.TestCase):

    def test_from_json(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/capability_behavior.json"))).read()
        d = Capability(json=data)

        assert d.vss == 5.0
        assert d.variance == 0.0
        assert d.non_swim_turning == "random"
        assert d.swim_turning == "random"
        assert d.calc_vss() == 5.0

    def test_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/capability_behavior.json"))).read()
        d = Capability(data=json.loads(data))

        assert d.vss == 5.0
        assert d.variance == 0.0
        assert d.non_swim_turning == "random"
        assert d.swim_turning == "random"
        assert d.calc_vss() == 5.0

    def test_variance(self):
        d = Capability()
        d.vss = 4.0
        d.variance = 0.5

        max_deviation = d.variance * 6

        assert d.calc_vss() >= d.vss - max_deviation
        assert d.calc_vss() <= d.vss + max_deviation