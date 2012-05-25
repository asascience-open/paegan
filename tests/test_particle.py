import unittest
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D

class ParticleTest(unittest.TestCase):
    def test_particle_linestring(self):
        p = Particle()
        p.location = Location4D(latitude=38, longitude=-76, depth=0)
        p.location = Location4D(latitude=39, longitude=-75, depth=1)
        p.location = Location4D(latitude=40, longitude=-74, depth=2)
       
        result = list(p.linestring().coords)
        assert (-76, 38, 0) == result[0]
        assert (-75, 39, 1) == result[1]
        assert (-74, 40, 2) == result[2]
        
    def test_particle_linestring_length(self):
        p = Particle()
        p.location = Location4D(latitude=38, longitude=-76, depth=0)
        p.location = Location4D(latitude=39, longitude=-75, depth=1)
        p.location = Location4D(latitude=40, longitude=-74, depth=2)
       
        assert(len(list(p.linestring().coords))) == 3

        p.location= Location4D(latitude=39, longitude=-75, depth=1)

        assert(len(list(p.linestring().coords))) == 4

    def test_particle_last_movement(self):
        p = Particle()
        p.location = Location4D(latitude=38, longitude=-76, depth=0)
        p.location = Location4D(latitude=39, longitude=-75, depth=1)
        p.location = Location4D(latitude=40, longitude=-74, depth=2)
       
        result = list(p.get_last_movement().coords)
        assert (-75, 39, 1) == result[0]
        assert (-74, 40, 2) == result[1]