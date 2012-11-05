import unittest
from paegan.transport.particles.particle import Particle, LarvaParticle
from paegan.transport.location4d import Location4D
from datetime import datetime, timedelta
import pytz

class ParticleTest(unittest.TestCase):

    def setUp(self):
        self.p = Particle()
        self.p.location = Location4D(latitude=38, longitude=-76, depth=0)
        self.p.location = Location4D(latitude=39, longitude=-75, depth=1)
        self.p.location = Location4D(latitude=40, longitude=-74, depth=2)

    def test_particle_linestring(self):
        result = list(self.p.linestring().coords)
        assert (-76, 38, 0) == result[0]
        assert (-75, 39, 1) == result[1]
        assert (-74, 40, 2) == result[2]
        
    def test_particle_linestring_length(self):      
        assert(len(list(self.p.linestring().coords))) == 3
        self.p.location= Location4D(latitude=39, longitude=-75, depth=1)
        assert(len(list(self.p.linestring().coords))) == 4

    def test_particle_last_movement(self):
        result = list(self.p.get_last_movement().coords)
        assert (-75, 39, 1) == result[0]
        assert (-74, 40, 2) == result[1]

    def test_particle_age(self):
        assert self.p.get_age(units='seconds') == 0
        assert self.p.get_age() == 0

        self.p.age(days=1)
        assert self.p.get_age(units='minutes') == 24 * 60
        assert self.p.get_age() == 1
        
        self.p.age(days=1)
        assert self.p.get_age(units='hours') == 48
        assert self.p.get_age() == 2

    def test_normalization(self):
        p = Particle()

        dt = datetime(2012, 8, 15, 0, tzinfo=pytz.utc)
        norms =[dt]

        last_real_movement = Location4D(latitude=38, longitude=-76, depth=0, time=dt)

        p.location = Location4D(latitude=100, longitude=-100, depth=0, time=dt)
        p.location = Location4D(latitude=101, longitude=-101, depth=0, time=dt)
        p.location = last_real_movement

        for x in xrange(1,10):
            norm = (dt + timedelta(hours=x)).replace(tzinfo=pytz.utc)
            norms.append(norm)
            p.location = Location4D(latitude=38 + x, longitude=-76 + x, depth=x, time=norm)
            
        locs = p.normalized_locations(norms)
        assert locs[0] == last_real_movement

class LarvaParticleTest(unittest.TestCase):

    def setUp(self):
        self.p = LarvaParticle()

    def test_growth(self):
        assert self.p.lifestage_index == 0
        self.p.grow(0.5)
        assert self.p.lifestage_index == 0
        self.p.grow(0.5)
        assert self.p.lifestage_index == 1
        self.p.grow(0.5)
        assert self.p.lifestage_index == 1
        assert self.p.lifestage_progress == 1.5

    def test_over_growth(self):
        self.p.grow(1.5)
        assert self.p.lifestage_index == 1
        assert self.p.lifestage_progress == 1.5
        self.p.grow(1.6)
        assert self.p.lifestage_progress == 3.1
        assert self.p.lifestage_index == 3
        