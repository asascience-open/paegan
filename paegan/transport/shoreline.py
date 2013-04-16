import os
import math
import time
import numpy as np
from osgeo import ogr
from gdalconst import *
from shapely import wkb, geometry
from shapely.geometry import LineString
from shapely.geometry import Point, Polygon
from shapely.geometry import MultiLineString
from shapely.geometry import MultiPolygon
from paegan.utils.asagreatcircle import AsaGreatCircle
from paegan.utils.asamath import AsaMath
from paegan.utils.asarandom import AsaRandom
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from shapely.prepared import prep

from paegan.logger import logger

class Shoreline(object):
    def __init__(self, **kwargs):
        """
            Optional named arguments: 
            * file (local path to OGC complient file)

            MUST BE land polygons!!
        """

        if kwargs.get("file") is not None:
            self._file = os.path.normpath(kwargs.pop('file'))
        else:
            self._file = os.path.normpath(os.path.join(__file__,"../../resources/shoreline/global/10m_land.shp"))

        point = kwargs.pop("point", None)
        self._spatialbuffer = kwargs.pop("spatialbuffer", 1)

        self._source = ogr.Open(self._file, GA_ReadOnly)
        if not self._source:
            raise Exception('Could not load {}'.format(self._file))

        self._type = kwargs.pop("type", "reverse")
        self._layer = self._source.GetLayer()
        self._geoms = []
        self.index(point=point)

    def close(self):
        # Srsly. Per GDAL docs this is how we should close the dataset.
        self._source = None

    def get_geoms(self):
        return self._geoms
    geoms = property(get_geoms, None)

    def get_linestring(self):
        points = []
        for poly in self._geoms:
            plines = list(poly.exterior.coords)
            for i in xrange(0,len(plines)-1):
                points.append(Point(plines[i], plines[i+1]))

            points.append(Point(np.nan, np.nan)) # blank point needed to remove crossing of lines
        return LineString(map(lambda x: list(x.coords)[0], points))
    linestring = property(get_linestring, None)

    def index(self, **kwargs):
        """
            This queries the shapefile around a buffer of a point
            The results of this spatial query are used for shoreline detection.

            Using the entire shapefile without the spatial query takes over
            30 times the time with world land polygons.

        """

        point = kwargs.pop("point", None)
        spatialbuffer = kwargs.pop("spatialbuffer", self._spatialbuffer)

        self._layer.SetSpatialFilter(None)
        self._spatial_query_object = None
        
        if point:
            self._spatial_query_object = point.buffer(spatialbuffer)
            poly = ogr.CreateGeometryFromWkt(self._spatial_query_object.wkt)
            self._layer.SetSpatialFilter(poly)
            poly.Destroy()

        self._geoms = []
        # The _geoms should be only Polygons, not MultiPolygons
        for element in self._layer:
            try:
                geom = wkb.loads(element.GetGeometryRef().ExportToWkb())
                if isinstance(geom, Polygon):
                    self._geoms.append(geom)
                elif isinstance(geom, MultiPolygon):
                    for poly in geom:
                        self._geoms.append(poly)
            except:
                logger.warn("Could not find valid geometry in shoreline element.  Point: %s, Buffer: %s" % (str(point), str(spatialbuffer)))

    def intersect(self, **kwargs):
        """
            Intersect a Line or Point Collection and the Shoreline

            Returns the point of intersection along the coastline
            Should also return a linestring buffer around the interseciton point
            so we can calculate the direction to bounce a particle.
        """
        ls = None

        if "linestring" in kwargs:
            ls = kwargs.pop('linestring')
            spoint = Point(ls.coords[0])
            epoint = Point(ls.coords[-1])
        elif "start_point" and "end_point" in kwargs:
            spoint = kwargs.get('start_point')
            epoint = kwargs.get('end_point')
            ls = LineString(list(spoint.coords) + list(epoint.coords))
        elif "single_point" in kwargs:
            spoint = kwargs.get('single_point')
            epoint = None
            ls = LineString(list(spoint.coords) + list(spoint.coords))
        else:
            raise TypeError( "must provide a LineString geometry object, (2) Point geometry objects, or (1) Point geometry object" )

        inter = False

        # If the current point lies outside of our current shapefile index,
        # re-query the shapefile in a buffer around this point
        if self._spatial_query_object and not ls.within(self._spatial_query_object):
            self.index(point=spoint)

        for element in self._geoms:
            prepped_element = prep(element)

            # Test if starting on land
            if prepped_element.contains(spoint):
                if epoint is None:
                    # If we only passed in one point, return the intersection is true.
                    return {'point': spoint, 'feature': None}
                else:
                    # If we are testing a linestring, raise an exception that we started on land.
                    raise Exception('Starting point on land')
            else:
                # If we are just checking a single point, continue looping.
                if epoint is None:
                    continue

            inter = ls.intersection(element)
            if inter:
                # Return the first point in the linestring, and the linestring that it hit
                if isinstance(inter, MultiLineString):
                    inter = inter.geoms[0]

                inter = Point(inter.coords[0])
                smaller_int = inter.buffer(self._spatialbuffer)
                shorelines = element.exterior.intersection(smaller_int)
                if isinstance(shorelines, LineString):
                    shorelines = [shorelines]
                else:
                    shorelines = list(shorelines)

                for shore_segment in shorelines:
                    # Once we find the linestring in the Polygon that was
                    # intersected, break out and return
                    if ls.touches(shore_segment):
                        break

                return {'point': Point(inter.x, inter.y, 0), 'feature': shore_segment or None}
        return None

    def react(self, **kwargs):
        """
            Bounce off of a shoreline
            feature = Linestring of two points, being the line segment the particle hit.
            angle = decimal degrees from 0 (x-axis), couter-clockwise (math style)
        """
        if self._type == "bounce":
            print "This shoreline type is NOT SUPPORTED and is broken"
            return self.__bounce(**kwargs)
        elif self._type == "reverse":
            return self.__reverse(**kwargs)
        else:
            return kwargs.get('hit_point')
            print "Not reacting to shoreline (sticky with inifinite concentration)"

    def __bounce(self, **kwargs):
        """
            Bounce off of the shoreline.

            NOTE: This does not work, but left here for future implementation

            feature = Linestring of two points, being the line segment the particle hit.
            angle = decimal degrees from 0 (x-axis), couter-clockwise (math style)
        """
        start_point = kwargs.pop('start_point')
        hit_point = kwargs.pop('hit_point')
        end_point = kwargs.pop('end_point')
        feature = kwargs.pop('feature')
        distance = kwargs.pop('distance')
        angle = kwargs.pop('angle')

        # Figure out the angle of the shoreline here (beta)
        points_in_shore = map(lambda x: Point(x), list(feature.coords))
        points_in_shore = sorted(points_in_shore, key=lambda x: x.x)

        # The point on the left (least longitude is always the first Point)
        first_shore = points_in_shore[0]
        last_shore = points_in_shore[-1]

        shoreline_x = abs(abs(first_shore.x) - abs(last_shore.x))
        shoreline_y = abs(abs(first_shore.y) - abs(last_shore.y))
        beta = math.degrees(math.atan(shoreline_x / shoreline_y))

        theta = 90 - angle - beta
        bounce_azimuth = AsaMath.math_angle_to_azimuth(angle=2 * theta + angle)

        print "Beta:           " + str(beta)
        print "Incoming Angle: " + str(angle)
        print "ShorelineAngle: " + str(theta + angle)
        print "Bounce Azimuth: " + str(bounce_azimuth)
        print "Bounce Angle:   " + str(AsaMath.azimuth_to_math_angle(azimuth=bounce_azimuth))

        after_distance = distance - AsaGreatCircle.great_distance(start_point=start_point, end_point=hit_point)['distance']
        
        new_point = AsaGreatCircle.great_circle(distance=after_distance, azimuth=bounce_azimuth, start_point=hit_point)
        return Location4D(latitude=new_point['latitude'], longitude=new_point['longitude'], depth=start_point.depth)

    def __reverse(self, **kwargs):
        """
            Reverse particle just off of the shore in the direction that it came in.
            Adds a slight random factor to the distance and angle it is reversed in.
        """
        start_point = kwargs.pop('start_point')
        hit_point = kwargs.pop('hit_point')
        distance = kwargs.pop('distance')
        azimuth = kwargs.pop('azimuth')
        reverse_azimuth = kwargs.pop('reverse_azimuth')
        reverse_distance = kwargs.get('reverse_distance', None)
        if reverse_distance is None:
            reverse_distance = 100

        # Randomize the reverse angle slightly (+/- 5 degrees)
        random_azimuth = reverse_azimuth + AsaRandom.random() * 5

        count = 0
        nudge_distance = 0.01
        nudge_point = AsaGreatCircle.great_circle(distance=nudge_distance, azimuth=reverse_azimuth, start_point=hit_point)
        nudge_loc = Location4D(latitude=nudge_point['latitude'], longitude=nudge_point['longitude'], depth=start_point.depth)

        # Find point just offshore to do testing with.  Try 15 times (~350m).  This makes sure the start_point is in the water
        # for the next call to intersect (next while loop).
        while self.intersect(single_point=nudge_loc.point) and count < 16:
            nudge_distance *= 2
            nudge_point = AsaGreatCircle.great_circle(distance=nudge_distance, azimuth=reverse_azimuth, start_point=hit_point)
            nudge_loc = Location4D(latitude=nudge_point['latitude'], longitude=nudge_point['longitude'], depth=start_point.depth)
            count += 1

        # We tried 16 times and couldn't find a point.  This should totally never happen.
        if count == 16:
            logger.debug("WOW. Could not find location in water to do shoreline calculation with.  Assuming particle did not move from original location")
            return start_point

        # Keep trying to throw particle back, halfing the distance each time until it is in water.
        # Only half it 12 times before giving up and returning the point which the particle came from.
        count = 0
        # Distance amount to half each iteration
        changing_distance = reverse_distance
        new_point = AsaGreatCircle.great_circle(distance=reverse_distance, azimuth=random_azimuth, start_point=hit_point)
        new_loc = Location4D(latitude=new_point['latitude'], longitude=new_point['longitude'], depth=start_point.depth)
        while self.intersect(start_point=nudge_loc.point, end_point=new_loc.point) and count < 12:
            changing_distance /= 2
            new_point = AsaGreatCircle.great_circle(distance=changing_distance, azimuth=random_azimuth, start_point=hit_point)
            new_loc = Location4D(latitude=new_point['latitude'], longitude=new_point['longitude'], depth=start_point.depth)
            count += 1

        # We tried 10 times and the particle was still on shore, return the point the particle started from.
        # No randomization.
        if count == 12:
            logger.debug("Could not react particle with shoreline.  Assuming particle did not move from original location")
            return start_point

        return new_loc
