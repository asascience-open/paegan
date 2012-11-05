import unittest
from paegan.transport.models.behaviors.lifestage import LifeStage
import os
import json
from datetime import datetime, timedelta
import pytz
from paegan.transport.location4d import Location4D
from paegan.transport.particles.particle import LarvaParticle
import random

class LifeStageTest(unittest.TestCase):

    def setUp(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/lifestage_single.json"))).read()
        self.lifestage = LifeStage(json=data)

        start_lat = 38
        start_lon = -76
        start_depth = -5
        temp_time = datetime.utcnow()
        self.start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        self.loc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=self.start_time)

        self.particles = []
        # Create particles
        for i in xrange(0,3):
            p = LarvaParticle()
            p.location = self.loc
            self.particles.append(p)

        # 48 timesteps at an hour each = 2 days of running
        self.times = range(0,172800,3600) # in seconds
        self.temps = []
        self.salts = []
        for w in xrange(0,48):
            self.temps.append(random.randint(20,40))
            self.salts.append(random.randint(10,30))

    def test_no_diel(self):
        data = json.loads(open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/lifestage_single.json"))).read())
        data['diel'] = []
        self.lifestage = LifeStage(data=data)

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
                movement = self.lifestage.move(p, 0, 0, 0, modelTimestep, temperature=self.temps[i], salinity=self.salts[i])
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

            # Lifestages currently influence the Z direction, so a particle should not
            # move horizontally.
            assert p.linestring().coords[-1][0] == self.loc.longitude
            assert p.linestring().coords[-1][1] == self.loc.latitude

    def test_moving_particle_with_lifestage(self):

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
                movement = self.lifestage.move(p, 0, 0, 0, modelTimestep, temperature=self.temps[i], salinity=self.salts[i])
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

            # Lifestages currently influence the Z direction, so a particle should not
            # move horizontally.
            assert p.linestring().coords[-1][0] == self.loc.longitude
            assert p.linestring().coords[-1][1] == self.loc.latitude
            
    def test_from_json(self):

        assert self.lifestage.name == 'third'
        assert self.lifestage.duration == 3
        assert self.lifestage.linear_a == 0.03
        assert self.lifestage.linear_b == 0.2
        assert len(self.lifestage.taxis) == 2
        assert self.lifestage.taxis[0].min_value == -30.0
        assert self.lifestage.taxis[0].max_value == -40.0        
        assert len(self.lifestage.diel) == 2
        assert self.lifestage.diel[0].min_depth == -2.0
        assert self.lifestage.diel[0].max_depth == -4.0
        assert self.lifestage.capability.vss == 5.0
        assert self.lifestage.capability.variance == 2.0
        assert self.lifestage.capability.non_swim_turning == 'random'
        assert self.lifestage.capability.swim_turning == 'random'

        t = datetime.utcnow().replace(tzinfo=pytz.utc)
        loc = Location4D(time=t, latitude=35, longitude=-76)
        assert isinstance(self.lifestage.diel[0].get_time(loc4d=loc), datetime)

    def test_from_dict(self):
        data = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/lifestage_single.json"))).read()
        l = LifeStage(data=json.loads(data))

        assert l.name == 'third'
        assert l.duration == 3
        assert l.linear_a == 0.03
        assert l.linear_b == 0.2
        assert len(l.taxis) == 2
        assert l.taxis[1].min_value == -30.0
        assert l.taxis[1].max_value == -50.0        
        assert len(l.diel) == 2
        assert l.diel[1].min_depth == -2.0
        assert l.diel[1].max_depth == -5.0
        assert l.capability.vss == 5.0
        assert l.capability.variance == 2.0
        assert l.capability.non_swim_turning == 'random'
        assert l.capability.swim_turning == 'random'

        t = datetime.utcnow().replace(tzinfo=pytz.utc)
        loc = Location4D(time=t, latitude=35, longitude=-76)
        assert isinstance(l.diel[0].get_time(loc4d=loc), datetime)