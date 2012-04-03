import unittest
from src.transport.location4d import Location4D
from src.transport.shoreline import Shoreline
from shapely.geometry import Point

class ShorelineTest(unittest.TestCase):

    def test_water_start_land_end_intersection(self):
        # Starts in the water and ends on land
        s = Shoreline()

        # -75, 39   is in the middle of the Delaware Bay
        # -75, 39.5 is on land
        # Intersection should be a Point starting somewhere around -75, 39.185 -> 39.195
        starting = Location4D(latitude=39, longitude=-75, depth=0).point
        ending   = Location4D(latitude=39.5, longitude=-75, depth=0).point

        intersection = s.intersect(start_point=starting, end_point=ending)
        assert -75 == intersection.x
        assert intersection.y > 39.185
        assert intersection.y < 39.195

    def test_land_start_water_end_intersection(self):
        # Starts on land and ends in the water
        s = Shoreline()

        # -75, 39.5 is on land
        # -75, 39   is in the middle of the Delaware Bay
        starting = Location4D(latitude=39.5, longitude=-75, depth=0).point
        ending   = Location4D(latitude=39, longitude=-75, depth=0).point

        self.assertRaises(Exception, s.intersect, start_point=starting, end_point=ending)

    def test_land_start_land_end_intersection(self):
        # Starts on land and ends on land
        s = Shoreline()

        # -75, 39.4 is on land
        # -75, 39.5 is on land
        starting = Location4D(latitude=39.4, longitude=-75, depth=0).point
        ending   = Location4D(latitude=39.5, longitude=-75, depth=0).point

        self.assertRaises(Exception, s.intersect, start_point=starting, end_point=ending)


    def test_water_start_water_end_jump_over_land_intersection(self):
        # Starts on water and ends on water, but there is land inbetween
        s = Shoreline()

        # -75, 39   is in the middle of the Delaware Bay
        # -74, 39   is in the Atlantic
        # This jumps over a peninsula.
        # Intersection should be the Point -74.96 -> -74.94, 39
        #
        starting = Location4D(latitude=39, longitude=-75, depth=0).point
        ending   = Location4D(latitude=39, longitude=-74, depth=0).point

        intersection = s.intersect(start_point=starting, end_point=ending)

        assert 39 == intersection.y
        assert intersection.x > -74.96
        assert intersection.x < -74.94
