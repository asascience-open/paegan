# encoding: utf-8

import unittest
from paegan.transport.models.behaviors.taxis import Taxis
import os
import json

class TaxisTest(unittest.TestCase):

    def test_salt_from_json(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/taxis_salinity.json"))).read()
        d = Taxis(json=data)

        assert d.gradient == 8
        assert d.units == "PSU"
        assert d.variable == "sea_water_salinity"
        assert d.min_value == 30.0
        assert d.max_value == 40.0

    def test_salt_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/taxis_salinity.json"))).read()
        d = Taxis(data=json.loads(data))

        assert d.gradient == 8
        assert d.units == "PSU"
        assert d.variable == "sea_water_salinity"
        assert d.min_value == 30.0
        assert d.max_value == 40.0

    def test_temp_from_json(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/taxis_temperature.json"))).read()
        d = Taxis(json=data)

        assert d.gradient == 8.0
        assert d.units == u"°C"
        assert d.variable == "sea_water_temperature"
        assert d.min_value == 30.0
        assert d.max_value == 40.0

    def test_temp_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/taxis_temperature.json"))).read()
        d = Taxis(data=json.loads(data))

        assert d.gradient == 8.0
        assert isinstance(d.units, unicode)
        assert d.units == u"°C"
        assert d.variable == "sea_water_temperature"
        assert d.min_value == 30.0
        assert d.max_value == 40.0