import unittest
from paegan.transport.models.behaviors.capability import Capability
import os
import json

class CapabilityTest(unittest.TestCase):

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

    def test_gaussian_variance(self):
        d = Capability()
        d.vss = 4.0
        d.variance = 0.5

        max_deviation = d.variance * 6

        real_vss = d.calc_vss(method='gaussian')
        assert real_vss >= d.vss - max_deviation
        assert real_vss <= d.vss + max_deviation

    def test_random_variance(self):
        d = Capability()
        d.vss = 4.0
        d.variance = 0.5

        real_vss = d.calc_vss(method='random')
        assert real_vss >= d.vss - d.variance
        assert real_vss <= d.vss + d.variance

    def test_error_variance(self):
        d = Capability()
        d.vss = 4.0
        d.variance = 0.5

        # Should result in a ValueError
        try:
            d.calc_vss(method='nada')
        except ValueError:
            assert True
        else:
            assert False