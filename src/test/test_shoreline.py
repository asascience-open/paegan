import unittest
from src.transport.location4d import Location4D
from src.transport.shoreline import Shoreline
from shapely.geometry import Point

class ShorelineTest(unittest.TestCase):
    def test_shoreline_loading(self):
        assert True
        
    def test_linestring_intersection(self):
        s = Shoreline()

        # -75, 39   is in the middle of the Delaware Bay
        # -75, 39.5 is on land.
        # Intersection should be on the -79 longitude and somewhere between 39.185 and 39.195
        starting = Location4D(latitude=39, longitude=-75, depth=0).point
        ending = Location4D(latitude=39.5, longitude=-75, depth=0).point

        intersection = Point(s.intersect(start_point= starting, end_point=ending).coords[0])
        assert -75 == intersection.x
        assert intersection.y > 39.185
        assert intersection.y < 39.195