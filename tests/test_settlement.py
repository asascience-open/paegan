import unittest
from paegan.transport.models.behaviors.settlement import Settlement
from paegan.transport.particles.particle import LarvaParticle
from paegan.transport.location4d import Location4D
import os
from datetime import datetime
import json

class SettlementTest(unittest.TestCase):

    def setUp(self):
        self.data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/settlement_behavior.json"))).read()

        temp_time = datetime.utcnow()
        self.start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        # 48 timesteps at an hour each = 2 days of running
        self.times = range(0,172800,3600) # in seconds

    def test_from_json(self):
        d = Settlement(json=self.data)

        assert d.type == 'benthic'
        assert d.upper == -100.0
        assert d.lower == -200.0

    def test_from_dict(self):
        d = Settlement(data=json.loads(self.data))

        assert d.type == 'benthic'
        assert d.upper == -100.0
        assert d.lower == -200.0

    def test_attempts(self):
        start_lat = 38
        start_lon = -76

        settle = Settlement(json='{"upper": 100.0, "lower": 200.0, "type": "benthic"}')
        # Particle above the upper bound
        particle = LarvaParticle()
        particle.location = Location4D(latitude=start_lat, longitude=start_lon, depth=-50, time=self.start_time)
        # Set bathymetry BETWEEN lower (200) and upper (100)
        settle.attempt(particle, -150)
        # We should have moved vertically to the bottom and settled
        assert particle.location.depth == -150
        assert particle.location.latitude == particle.locations[-2].latitude
        assert particle.location.longitude == particle.locations[-2].longitude
        assert particle.location.time == particle.locations[-2].time
        assert particle.settled


        settle = Settlement(json='{"upper": 100.0, "lower": 200.0, "type": "benthic"}')
        # Particle above the upper bound
        particle = LarvaParticle()
        particle.location = Location4D(latitude=start_lat, longitude=start_lon, depth=-250, time=self.start_time)
        # Set bathymetry BELOW lower (200) and upper (100)
        settle.attempt(particle, -400)
        # We should not have moved
        assert len(particle.locations) == 1
        assert not particle.settled


        settle = Settlement(json='{"upper": 100.0, "lower": 200.0, "type": "pelagic"}')
        # Particle above the upper bound
        particle = LarvaParticle()
        particle.location = Location4D(latitude=start_lat, longitude=start_lon, depth=-50, time=self.start_time)
        # Set bathymetry BELOW lower (200) and upper (100)
        settle.attempt(particle, -400)
        # We should not have moved
        assert len(particle.locations) == 1
        assert not particle.settled


        settle = Settlement(json='{"upper": 100.0, "lower": 200.0, "type": "pelagic"}')
        # Particle is between the upper and lower bounds
        particle = LarvaParticle()
        particle.location = Location4D(latitude=start_lat, longitude=start_lon, depth=-150, time=self.start_time)
        # Set bathymetry BELOW lower (200) and upper (100)
        settle.attempt(particle, -400)
        # We should have settled, but not moved anywhere
        assert len(particle.locations) == 1
        assert particle.settled    