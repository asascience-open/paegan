import unittest
from paegan.transport.location4d import Location4D
from paegan.transport.shoreline import Shoreline
from shapely.geometry import Point
from paegan.utils.asagreatcircle import AsaGreatCircle
from paegan.utils.asamath import AsaMath
import math
import time
import os

class ShorelineTest(unittest.TestCase):

    def setUp(self):
        self.shoreline_path = "/data/lm/shore"

    def test_reindexing(self):

        p = Point(-73.745631, 40.336791)
        p2 = Point(-78.745631, 44.336791)
        p3 = Point(0, 0)
        st = time.time()
        s = Shoreline(point=p, spatialbuffer=2)
        s.index(point=p2, spatialbuffer=2)
        s.index(point=p3, spatialbuffer=2)
        print "Reindexing Time: " + str(time.time() - st)
        
    def test_large_shape_reindexing(self):

        p = Point(-73.745631, 40.336791)
        p2 = Point(-78.745631, 44.336791)
        p3 = Point(0, 0)
        st = time.time()
        shore_path = os.path.join(self.shoreline_path, "alaska", "AK_Land_Basemap.shp")
        s = Shoreline(file=shore_path, point=p, spatialbuffer=0.25)
        s.index(point=p2, spatialbuffer=0.25)
        s.index(point=p3, spatialbuffer=0.25)
        print "Large Shoreline Reindexing Time: " + str(time.time() - st)

    def test_multipart_shape_reindexing(self):

        p = Point(-73.745631, 40.336791)
        p2 = Point(-78.745631, 44.336791)
        p3 = Point(0, 0)
        st = time.time()
        shore_path = os.path.join(self.shoreline_path, "westcoast", "New_Land_Clean.shp")
        s = Shoreline(file=shore_path, point=p, spatialbuffer=1)
        s.index(point=p2, spatialbuffer=0.25)
        s.index(point=p3, spatialbuffer=0.25)
        print "Multipart Shoreline Reindexing Time: " + str(time.time() - st)

    def test_intersection_speed(self):

        # Intersects on the west coast of NovaScotia

        starting = Location4D(longitude=-66.1842219282406177, latitude=44.0141581697495852, depth=0).point
        ending = Location4D(longitude=-66.1555195384399326, latitude=44.0387992322117370, depth=0).point
        s = Shoreline(point=starting, spatialbuffer=1)

        st = time.time()
        intersection = s.intersect(start_point=starting, end_point=ending)['point']
        print "Intersection Time: " + str(time.time() - st)

    def test_large_shape_intersection_speed(self):

        # Intersects on the west coast of NovaScotia

        starting = Location4D(longitude=-146.62, latitude=60.755, depth=0).point
        ending = Location4D(longitude=-146.60, latitude=60.74, depth=0).point
        shore_path = os.path.join(self.shoreline_path, "alaska", "AK_Land_Basemap.shp")
        s = Shoreline(file=shore_path, point=starting, spatialbuffer=0.25)

        st = time.time()
        intersection = s.intersect(start_point=starting, end_point=ending)['point']
        print "Large Shoreline Intersection Time: " + str(time.time() - st)

    def test_multipart_shape_intersection_speed(self):

        # Intersects on the west coast of NovaScotia

        starting = Location4D(longitude=-146.62, latitude=60.755, depth=0).point
        ending = Location4D(longitude=-146.60, latitude=60.74, depth=0).point
        shore_path = os.path.join(self.shoreline_path, "westcoast", "New_Land_Clean.shp")
        s = Shoreline(file=shore_path, point=starting, spatialbuffer=1)

        st = time.time()
        intersection = s.intersect(start_point=starting, end_point=ending)['point']
        print "Multipart Shoreline Intersection Time: " + str(time.time() - st)

    def test_water_start_land_end_intersection(self):
        # Starts in the water and ends on land
        s = Shoreline()

        # -75, 39   is in the middle of the Delaware Bay
        # -75, 39.5 is on land
        # Intersection should be a Point starting somewhere around -75, 39.185 -> 39.195
        starting = Location4D(latitude=39, longitude=-75, depth=0).point
        ending   = Location4D(latitude=39.5, longitude=-75, depth=0).point

        intersection = Location4D(point=s.intersect(start_point=starting, end_point=ending)['point'])
        assert -75 == intersection.longitude
        assert intersection.latitude > 39.185
        assert intersection.latitude < 39.195

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

        intersection = Location4D(point=s.intersect(start_point=starting, end_point=ending)['point'])

        assert 39 == intersection.latitude
        assert intersection.longitude > -74.96
        assert intersection.longitude < -74.94

    def test_reverse_left(self):

        s = Shoreline(type='reverse')

        starting = Location4D(latitude=39.1, longitude=-74.91, depth=0)
        ending   = Location4D(latitude=39.1, longitude=-74.85, depth=0)

        difference = AsaGreatCircle.great_distance(start_point=starting, end_point=ending)
        angle = AsaMath.azimuth_to_math_angle(azimuth=difference['azimuth'])
        distance = difference['distance']

        intersection = s.intersect(start_point=starting.point, end_point=ending.point)
        int4d = Location4D(point=intersection['point'])

        final_point = s.react(  start_point = starting,
                                hit_point = int4d,
                                end_point = ending,
                                feature = intersection['feature'],
                                distance = distance,
                                angle = angle,
                                azimuth = difference['azimuth'],
                                reverse_azimuth = difference['reverse_azimuth'])

        # Since we are on a stright horizonal line, the latitude will change only slightly
        assert abs(final_point.latitude - starting.latitude) < 0.005

        # Resulting longitude should be between the startpoint and the intersection point
        assert final_point.longitude < int4d.longitude
        assert final_point.longitude > starting.longitude

    def test_reverse_up_left(self):

        s = Shoreline(type='reverse')

        starting = Location4D(latitude=39.05, longitude=-75.34, depth=0)
        ending   = Location4D(latitude=38.96, longitude=-75.315, depth=0)
        
        difference = AsaGreatCircle.great_distance(start_point=starting, end_point=ending)
        angle = AsaMath.azimuth_to_math_angle(azimuth=difference['azimuth'])
        distance = difference['distance']

        intersection = s.intersect(start_point=starting.point, end_point=ending.point)
        int4d = Location4D(point=intersection['point'])

        final_point = s.react(  start_point = starting,
                                hit_point = int4d,
                                end_point = ending,
                                feature = intersection['feature'],
                                distance = distance,
                                angle = angle,
                                azimuth = difference['azimuth'],
                                reverse_azimuth = difference['reverse_azimuth'])

        # Resulting latitude should be between the startpoint and the intersection point
        assert final_point.latitude > int4d.latitude
        assert final_point.latitude < starting.latitude
        
        # Resulting longitude should be between the startpoint and the intersection point
        assert final_point.longitude < int4d.longitude
        assert final_point.longitude > starting.longitude

    def test_reverse_half_distance_until_in_water(self):

        s = Shoreline(type='reverse')

        starting = Location4D(latitude=39.05, longitude=-75.34, depth=0)
        ending   = Location4D(latitude=38.96, longitude=-75.315, depth=0)
        
        difference = AsaGreatCircle.great_distance(start_point=starting, end_point=ending)
        angle = AsaMath.azimuth_to_math_angle(azimuth=difference['azimuth'])
        distance = difference['distance']

        intersection = s.intersect(start_point=starting.point, end_point=ending.point)
        int4d = Location4D(point=intersection['point'])

        final_point = s.react(  start_point = starting,
                                hit_point = int4d,
                                end_point = ending,
                                feature = intersection['feature'],
                                distance = distance,
                                angle = angle,
                                azimuth = difference['azimuth'],
                                reverse_azimuth = difference['reverse_azimuth'],
                                reverse_distance = 40000)

        # Should be in water
        assert s.intersect(start_point=final_point.point, end_point=final_point.point) is None

    def test_reverse_12_times_then_start_point(self):

        s = Shoreline(type='reverse')

        starting = Location4D(latitude=39.05, longitude=-75.34, depth=0)
        ending   = Location4D(latitude=38.96, longitude=-75.315, depth=0)
        
        difference = AsaGreatCircle.great_distance(start_point=starting, end_point=ending)
        angle = AsaMath.azimuth_to_math_angle(azimuth=difference['azimuth'])
        distance = difference['distance']

        intersection = s.intersect(start_point=starting.point, end_point=ending.point)
        int4d = Location4D(point=intersection['point'])

        final_point = s.react(  start_point = starting,
                                hit_point = int4d,
                                end_point = ending,
                                feature = intersection['feature'],
                                distance = distance,
                                angle = angle,
                                azimuth = difference['azimuth'],
                                reverse_azimuth = difference['reverse_azimuth'],
                                reverse_distance = 9999999999999999999999999999)

        # Should be start location
        assert final_point.longitude == starting.longitude
        assert final_point.latitude == starting.latitude
        assert final_point.depth == starting.depth

    def test_reverse_distance_traveled(self):

        s = Shoreline(type='reverse')

        starting = Location4D(latitude=39.05, longitude=-75.34, depth=0)
        ending   = Location4D(latitude=38.96, longitude=-75.315, depth=0)
        
        difference = AsaGreatCircle.great_distance(start_point=starting, end_point=ending)
        angle = AsaMath.azimuth_to_math_angle(azimuth=difference['azimuth'])
        distance = difference['distance']

        intersection = s.intersect(start_point=starting.point, end_point=ending.point)
        int4d = Location4D(point=intersection['point'])

        final_point = s.react(  start_point = starting,
                                hit_point = int4d,
                                end_point = ending,
                                feature = intersection['feature'],
                                distance = distance,
                                angle = angle,
                                azimuth = difference['azimuth'],
                                reverse_azimuth = difference['reverse_azimuth'],
                                reverse_distance = 0.000001)

        # Resulting point should be VERY close to the hit point.
        assert abs(int4d.latitude - final_point.latitude) < 0.005
        assert abs(int4d.longitude - final_point.longitude) < 0.005
