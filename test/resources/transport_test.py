import unittest
from transport.models.transport import Transport
from transport.particles.particle import Particle

class TransportTest(unittest.TestCase):

	def test_transport(self):
		p = Particle()

		p2 = Particle()

		p.set_next_location([-76, 36])
		print p.get_current_location()
		p.set_next_location([-70, 20])
		print p.get_current_location()
		print p.get_locations()

		times = [600, 1200, 1800]
		u = [0.6, 0.8, 0.7]
		v = [-1.2, -1.4, -0.7]

		for i in xrange(0,len(times)):
			location = Transport(p.get_current_location(), times[i], u[i], v[i])
			p.set_next_location(location)