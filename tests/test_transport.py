import unittest
import random
import numpy
from datetime import datetime, timedelta
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom

class TransportTest(unittest.TestCase):

    def setUp(self):
        start_lat = 38
        start_lon = -76
        start_depth = -5
        temp_time = datetime.utcnow()
        self.start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        self.loc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=self.start_time)
        
        # Generate time,u,v,z as randoms
        # 48 timesteps at an hour each = 2 days of running
        self.times = range(0,172800,3600) # in seconds
        self.u = []
        self.v = []
        self.z = []
        for w in xrange(0,48):
            self.z.append(random.gauss(0,0.0001)) # gaussian in m/s
            self.u.append(abs(AsaRandom.random())) # random function in m/s
            self.v.append(abs(AsaRandom.random())) # random function in m/s

        self.particles = []
        # Create particles
        for i in xrange(0,3):
            p = Particle()
            p.location = self.loc
            self.particles.append(p)

        # Create a transport instance with horiz and vert dispersions
        self.transport_model = Transport(horizDisp=0.05, vertDisp=0.00003)

    def test_moving_particle(self):

        for p in self.particles:
            for i in xrange(0, len(self.times)):
                try:
                    modelTimestep = self.times[i+1] - self.times[i]
                    calculatedTime = self.times[i+1]
                except StandardError:
                    modelTimestep = self.times[i] - self.times[i-1]
                    calculatedTime = self.times[i] + modelTimestep

                newtime = self.start_time + timedelta(seconds=calculatedTime)

                p.age(seconds=modelTimestep)
                movement = self.transport_model.move(p, self.u[i], self.v[i], self.z[i], modelTimestep)
                newloc = Location4D(latitude=movement['latitude'], longitude=movement['longitude'], depth=movement['depth'], time=newtime)
                p.location = newloc
            
        for p in self.particles:
            # Particle should move every timestep
            assert len(p.locations) == len(self.times) + 1
            # A particle should always move in this test
            assert len(set(p.locations)) == len(self.times) + 1
            # A particle should always age
            assert p.get_age(units='days') == (self.times[-1] + 3600) / 60. / 60. / 24.
            # First point of each particle should be the starting location
            assert p.linestring().coords[0][0] == self.loc.longitude
            assert p.linestring().coords[0][1] == self.loc.latitude
            assert p.linestring().coords[0][2] == self.loc.depth
