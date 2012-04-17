import math
import unittest
from src.transport.particles.particle import Particle
from src.utils.asagreatcircle import AsaGreatCircle
from src.utils.asamath import AsaMath
from src.transport.location4d import Location4D

class GreatCircleTest(unittest.TestCase):
    def test_great_circle_angles(self):

        # One decimal degree is 111000m
        starting = Location4D(latitude=40.00, longitude=-76.00, depth=0)

        azimuth = 90
        new_gc = AsaGreatCircle.great_circle(distance=111000, azimuth=azimuth, start_point=starting)
        new_pt = Location4D(latitude=new_gc['latitude'], longitude=new_gc['longitude'])
        # We should have gone to the right
        assert new_pt.longitude > starting.longitude + 0.9

        azimuth = 270
        new_gc = AsaGreatCircle.great_circle(distance=111000, azimuth=azimuth, start_point=starting)
        new_pt = Location4D(latitude=new_gc['latitude'], longitude=new_gc['longitude'])
        # We should have gone to the left
        assert new_pt.longitude < starting.longitude - 0.9

        azimuth = 180
        new_gc = AsaGreatCircle.great_circle(distance=111000, azimuth=azimuth, start_point=starting)
        new_pt = Location4D(latitude=new_gc['latitude'], longitude=new_gc['longitude'])
        # We should have gone down
        assert new_pt.latitude < starting.latitude - 0.9

        azimuth = 0
        new_gc = AsaGreatCircle.great_circle(distance=111000, azimuth=azimuth, start_point=starting)
        new_pt = Location4D(latitude=new_gc['latitude'], longitude=new_gc['longitude'])
        # We should have gone up
        assert new_pt.latitude > starting.latitude + 0.9

        azimuth = 315
        new_gc = AsaGreatCircle.great_circle(distance=111000, azimuth=azimuth, start_point=starting)
        new_pt = Location4D(latitude=new_gc['latitude'], longitude=new_gc['longitude'])
        # We should have gone up and to the left
        assert new_pt.latitude > starting.latitude + 0.45
        assert new_pt.longitude < starting.longitude - 0.45
