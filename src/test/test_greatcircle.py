import math
import unittest
from src.transport.particles.particle import Particle
from src.utils.asagreatcircle import AsaGreatCircle
from src.transport.location4d import Location4D

class ParticleTest(unittest.TestCase):
    def test_1(self):

        # One decimal degree is 111000m
        starting = Location4D(latitude=40.00, longitude=-76.00, depth=0)

        angle = 0
        azimuth = 90 - angle
        if azimuth < 0:
            azimuth += 360
        new_gc = AsaGreatCircle.great_circle(distance=111000, angle=azimuth, start_point=starting)
        new_pt = Location4D(latitude=math.degrees(new_gc['latitude']), longitude=math.degrees(new_gc['longitude']))

        # We should have gone to the right
        assert new_pt.longitude > -76

        angle = 180
        azimuth = 90 - angle
        if azimuth < 0:
            azimuth += 360
        new_gc = AsaGreatCircle.great_circle(distance=111000, angle=azimuth, start_point=starting)
        new_pt = Location4D(latitude=math.degrees(new_gc['latitude']), longitude=math.degrees(new_gc['longitude']))

        # We should have gone to the left
        assert new_pt.longitude < -76

        angle = 270
        azimuth = 90 - angle
        if azimuth < 0:
            azimuth += 360
        new_gc = AsaGreatCircle.great_circle(distance=111000, angle=azimuth, start_point=starting)
        new_pt = Location4D(latitude=math.degrees(new_gc['latitude']), longitude=math.degrees(new_gc['longitude']))

        # We should have gone down
        assert new_pt.latitude < 40

        angle = 90
        azimuth = 90 - angle
        if azimuth < 0:
            azimuth += 360
        new_gc = AsaGreatCircle.great_circle(distance=111000, angle=azimuth, start_point=starting)
        new_pt = Location4D(latitude=math.degrees(new_gc['latitude']), longitude=math.degrees(new_gc['longitude']))

        # We should have gone up
        assert new_pt.latitude > 40