import unittest
import random
import matplotlib
import matplotlib.pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy
from datetime import datetime, timedelta
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom

class TransportTest(unittest.TestCase):
    def test_single_particle(self):
        p = Particle() # create a particle instance 'p'
        # Set the start position of the Particle
        start_lat = 38
        start_lon = -76
        start_depth = -5
        temp_time = datetime.utcnow()
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)

        loc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=start_time)
        p.location = loc # set particle location
        
        times = [0, 3600, 7200, 10800] # in seconds
        u = [0.3, 0.2, 0.1, 0.05] # in m/s
        v = [-0.1, -0.3, -0.06, -0.2] # in m/s
        z = [0.005, 0.002, 0.001, -0.003] # in m/s

        for i in xrange(0, len(times)):
            #print p.get_current_location()
            transport_model = Transport(horizDisp=0.05, vertDisp=0.00003) # create a transport instance with horiz and vert dispersions
            current_location = p.location
            try:
                modelTimestep = times[i+1] - times[i]
                calculatedTime = times[i+1]
            except:
                modelTimestep = times[i] - times[i-1]
                calculatedTime = times[i] + modelTimestep
            movement = transport_model.move(current_location, u[i], v[i], z[i], modelTimestep)
            newloc = Location4D(latitude=movement['latitude'], longitude=movement['longitude'], depth=movement['depth'])
            newloc.u = movement['u']
            newloc.v = movement['v']
            newloc.z = movement['z']
            newloc.time = start_time + timedelta(seconds=calculatedTime)
            p.location = newloc
            
        #print p.linestring()
        #for u in xrange(0,len(p.get_locations())):
        #    print p.get_locations()[u]

    def test_multiple_particles(self):
        # Constants
        times = range(0,360001,3600) # in seconds
        start_lat = 38
        start_lon = -76
        start_depth = -5
        temp_time = datetime.utcnow()
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        # empty array for storing particle objects
        arr = []
        # Generate u,v,z as random numbers
        u=[]
        v=[]
        z=[]
        for w in xrange(0,100):
            z.append(random.gauss(0,0.0001)) # gaussian in m/s
            u.append(abs(AsaRandom.random())) # random function in m/s
            v.append(abs(AsaRandom.random())) # random function in m/s

        for i in xrange(0,3):
            p = Particle()

            loc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=start_time)
            p.location = loc # set particle location

            for i in xrange(0, len(times)-1):
                #print t
                #print p.get_current_location()
                transport_model = Transport(horizDisp=0.05, vertDisp=0.00003) # create a transport instance
                current_location = p.location
                try:
                    modelTimestep = times[i+1] - times[i]
                    calculatedTime = times[i+1]
                except:
                    modelTimestep = times[i] - times[i-1]
                    calculatedTime = times[i] + modelTimestep
                movement = transport_model.move(current_location, u[i], v[i], z[i], modelTimestep)

                newloc = Location4D(latitude=movement['latitude'], longitude=movement['longitude'], depth=movement['depth'])
                newloc.u = movement['u']
                newloc.v = movement['v']
                newloc.z = movement['z']
                newloc.time = start_time + timedelta(seconds=calculatedTime)
                p.location = newloc
            arr.append(p)
            
            
