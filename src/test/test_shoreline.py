import unittest
from src.transport.location4d import Location4D
from src.transport.shoreline import Shoreline
from shapely.geometry import Point
from src.utils.asagreatcircle import AsaGreatCircle
import math

class ShorelineTest(unittest.TestCase):

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

    def test_water_start_water_end_jump_over_land_intersection_and_reaction(self):
        # Starts on water and ends on water, but there is land inbetween
        s = Shoreline()

        # -75, 39   is in the middle of the Delaware Bay
        # -74, 39   is in the Atlantic
        # This jumps over a peninsula.
        # Intersection should be the Point -74.96 -> -74.94, 39
        #
        starting = Location4D(latitude=39.1, longitude=-74.91, depth=0)
        ending   = Location4D(latitude=39.1, longitude=-74.85, depth=0)

        difference = AsaGreatCircle.great_distance(start_point=starting, end_point=ending)
        angle = difference['angle']
        distance = difference['distance']

        intersection = s.intersect(start_point=starting.point, end_point=ending.point)
        int4d = Location4D(point=intersection['point'])
        assert 39.1 == int4d.latitude
        assert int4d.longitude > -74.91
        assert int4d.longitude < -74.88

        # Distance until it hit shoreline.  Measured in Arc to be somewhere around 945 meters
        first_leg = AsaGreatCircle.great_distance(start_point=starting, end_point=int4d)
        assert first_leg['distance'] > 940
        assert first_leg['distance'] < 950

        # Second leg distance
        reaction_distance = distance - first_leg['distance']
        shoreline_angle = 65.44745 # Calculated with Arc
        # Coming in at 0 degrees and hitting an angle of 65.44745, resulting in 114.55255
        reaction_angle = shoreline_angle + 90 + angle

        second_point = AsaGreatCircle.great_circle(distance=reaction_distance, angle=math.radians(reaction_angle), start_point=int4d)
        second_location = Location4D(latitude=math.degrees(second_point['latitude']), longitude=math.degrees(second_point['longitude']), depth=ending.depth)

        # should have 'bounced' up and to the left
        assert second_location.latitude < int4d.latitude # left
        assert second_location.longitude > int4d.longitude # up

        # First leg plus second leg should equal total distance
        second_leg = AsaGreatCircle.great_distance(start_point=int4d, end_point=second_location)
        assert round(second_leg['distance'] + first_leg['distance'], 4) == round(distance, 4)