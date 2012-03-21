import unittest
from datetime import datetime, timedelta
from src.transport.models.transport import Transport
from src.transport.particles.particle import Particle
from src.transport.models.vincentydirect import vinc_pt
from src.transport.models.location4d import Location4D

class TransportTest(unittest.TestCase):
    def test_single_particle(self):
        p = Particle() # create a particle instance 'p'
        # Set the start position of the Particle
        start_lat = 38
        start_lon = -76
        start_depth = 4
        temp_time = datetime.utcnow()
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)

        loc = Location4D(start_lat, start_lon, start_depth)
        loc.time = start_time
        p.set_next_location(loc) # set particle location
        
        times = [0, 3600, 7200, 10800] # in seconds
        horizDisp=0.05 # in meters^2 / second
        vertDisp=0.00003 # in meters^2 / second
        u = [0.3, 0.2, 0.1, 0.05] # in m/s
        v = [-0.1, -0.3, -0.06, -0.2] # in m/s
        z = [0.005, 0.002, 0.001, -0.003] # in m/s

        for i in xrange(0, len(times)):
            #print p.get_current_location()
            transport_model = Transport() # create a transport instance
            current_location = p.get_current_location()
            try:
                modelTimestep = times[i+1] - times[i]
                calculatedTime = times[i+1]
            except:
                modelTimestep = times[i] - times[i-1]
                calculatedTime = times[i] + modelTimestep
            movement = transport_model.move(current_location.latitude, current_location.longitude, current_location.depth, u[i], v[i], z[i], horizDisp, vertDisp, modelTimestep)
            newloc = Location4D(movement['lat'], movement['lon'], movement['depth'])
            newloc.u = movement['u']
            newloc.v = movement['v']
            newloc.z = movement['z']
            newloc.time = start_time + timedelta(seconds=calculatedTime)
            p.set_next_location(newloc)
            
        #for u in xrange(0,len(p.get_locations())):
        #    print p.get_locations()[u]

    def test_multiple_particles(self):
        # Constants
        horizDisp=0.05 # in meters^2 / second
        vertDisp=0.00003 # in meters^2 / secon
        times = [0, 3600, 7200, 10800] # in seconds
        start_lat = 38
        start_lon = -76
        start_depth = 4
        temp_time = datetime.utcnow()
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)

        # Generate these as random numbers
        u = [0.3, 0.2, 0.1, 0.05] # in m/s
        v = [-0.1, -0.3, -0.06, -0.2] # in m/s
        z = [0.005, 0.002, 0.001, -0.003] # in m/s

        for i in xrange(0,100):
            p = Particle()
            for t in xrange(0, len(times)):
                print t
                # run transport