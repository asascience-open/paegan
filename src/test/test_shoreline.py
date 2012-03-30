import unittest
from src.transport.location4d import Location4D
from src.transport.shoreline import Shoreline

class ShorelineTest(unittest.TestCase):
    def test_shoreline_loading(self):
        assert True
        
    def test_linestring_intersection(self):
        s = Shoreline()
        starting = Location4D(latitude=20, longitude=-90, depth=0).point
        ending = Location4D(latitude=39, longitude=-75, depth=1).point

        intersections = s.intersect(start_point= starting, end_point=ending)
        print intersections