import unittest
from src.transport.models.transport import Transport
from src.transport.models.transport import genRand
from src.transport.particles.particle import Particle
from src.transport.models.vincentydirect import vinc_pt
from src.transport.models.location3d import Location3D

class TransportTest(unittest.TestCase):
    def test_transport(self):
        p = Particle() # create a particle instance 'p'
        p.set_next_location([-76, 38]) # set particle location
        p.set_next_velocity(6) # set particle velocity
        p.set_next_depth(4)
        times = [3600, 7200, 10800] # in seconds
        modelTimestep = times[1] - times[0] # in seconds
        horizDisp=0.05 # in meters
        vertDisp=0.03 # in meters
        u = [0.2, 0.1, 0.05] # in m/s
        v = [-0.3, -0.06, -0.2] # in m/s
        z = [0.002, 0.01, -0.012] # in m/s
        for i in xrange(0, len(times)):
            location = Transport() # create a transport instance 'location'
            position = Location3D()
            latitude = p.get_current_location()[1] # take the most recent latitude of the particle instance
            longitude = p.get_current_location()[0] # take the most recent longitude of the particle instance
            depth = p.get_current_depth()
            position.longitude, position.latitude, position.depth, position.velocity = location.move(latitude, longitude, times[i], u[i], v[i], z[i], depth, horizDisp, vertDisp, modelTimestep)
            p.set_next_location([position.longitude, position.latitude])
            p.set_next_velocity(position.velocity)
            p.set_next_depth(position.depth)
            print 'iteration', i
            print 'location', p.get_current_location()
            print 'velocity', p.get_current_velocity()
            print 'depth', p.get_current_depth()