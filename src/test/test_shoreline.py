import unittest
from src.transport.location4d import Location4D
from src.transport.shoreline import Shoreline
from shapely.geometry import Point
from src.utils.asagreatcircle import AsaGreatCircle
import math

class ShorelineTest(unittest.TestCase):

    def test_indexing(self):
        p = Point(-73.745631, 40.336791)
        s = Shoreline(point=p, spatialbuffer=2)

    def test_water_start_land_end_intersection(self):
        # Starts in the water and ends on land
        s = Shoreline()

        # -75, 39   is in the middle of the Delaware Bay
        # -75, 39.5 is on land
        # Intersection should be a Point starting somewhere around -75, 39.185 -> 39.195
        starting = Location4D(latitude=39, longitude=-75, depth=0).point
        ending   = Location4D(latitude=39.5, longitude=-75, depth=0).point

        intersection = s.intersect(start_point=starting, end_point=ending)['point']
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

        intersection = s.intersect(start_point=starting, end_point=ending)['point']

        assert 39 == intersection.y
        assert intersection.x > -74.96
        assert intersection.x < -74.94

    def test_reaction_up_left(self):

        s = Shoreline()

        starting = Location4D(latitude=39.1, longitude=-74.91, depth=0)
        ending   = Location4D(latitude=39.1, longitude=-74.85, depth=0)

        difference = AsaGreatCircle.great_distance(start_point=starting, end_point=ending)
        angle = math.degrees(difference['angle'])
        distance = difference['distance']

        intersection = s.intersect(start_point=starting.point, end_point=ending.point)
        int4d = Location4D(point=intersection['point'])

        final_point = s.react(  start_point = starting,
                                hit_point = int4d,
                                end_point = ending,
                                feature = intersection['feature'],
                                distance = distance,
                                angle = angle)

        # should have 'bounced' up and to the left
        assert final_point.latitude < int4d.latitude
        assert final_point.longitude > int4d.longitude

    def test_reaction_down_right(self):

        s = Shoreline()

        starting = Location4D(latitude=39.05, longitude=-75.34, depth=0)
        ending   = Location4D(latitude=38.96, longitude=-75.315, depth=0)

        difference = AsaGreatCircle.great_distance(start_point=starting, end_point=ending)
        angle = math.degrees(difference['angle'])
        distance = difference['distance']

        intersection = s.intersect(start_point=starting.point, end_point=ending.point)
        int4d = Location4D(point=intersection['point'])

        final_point = s.react(  start_point = starting,
                                hit_point = int4d,
                                end_point = ending,
                                feature = intersection['feature'],
                                distance = distance,
                                angle = angle)

        # should have 'bounced' up and to the left
        #assert final_point.latitude > int4d.latitude
        #assert final_point.longitude < int4d.longitude
