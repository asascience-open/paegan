import math
from paegan.external.greatcircle import GreatCircle
import numpy as np

class AsaGreatCircle(object):

    @classmethod
    def great_circle(self, **kwargs):
        """
            Named arguments:
            distance = distance to traveled
            azimuth = angle, in DECIMAL DEGREES of HEADING from NORTH
            start_point = Location4D object representing the starting point
            rmajor = radius of earth's major axis. default=6378137.0 (WGS84)
            rminor = radius of earth's minor axis. default=6356752.3142 (WGS84)

            Returns a dictionary with:
            'latitude' in decimal degrees
            'longitude' in decimal degrees
            'reverse_azimuth' in decimal degrees

        """

        distance = kwargs.pop('distance')
        azimuth = kwargs.pop('azimuth')
        starting = kwargs.pop('start_point')
        rmajor = kwargs.pop('rmajor', 6378137.0)
        rminor = kwargs.pop('rminor', 6356752.3142)
        f = (rmajor - rminor) / rmajor

        lat_result, lon_result, angle_result = GreatCircle.vinc_pt(f, rmajor, math.radians(starting.latitude), math.radians(starting.longitude), math.radians(azimuth), distance)

        return {'latitude': math.degrees(lat_result), 'longitude': math.degrees(lon_result), 'reverse_azimuth': math.degrees(angle_result)}

    @classmethod
    def great_distance(self, **kwargs):
        """
            Named arguments:
            start_point = Location4D obect representing start point
            end_point = Location4D obect representing end point
            rmajor = radius of earth's major axis. default=6378137.0 (WGS84)
            rminor = radius of earth's minor axis. default=6356752.3142 (WGS84)

            Returns a dictionaty with:
            'distance' in meters
            'azimuth' in decimal degrees
            'reverse_azimuth' in decimal degrees

        """

        start_point = kwargs.pop('start_point', None)
        end_point = kwargs.pop('end_point', None)
        if start_point == None and end_point == None:
            start_lat = kwargs.pop("start_lats")
            start_lon = kwargs.pop("start_lons")
            end_lat = kwargs.pop("end_lats")
            end_lon = kwargs.pop("end_lons")
        rmajor = kwargs.pop('rmajor', 6378137.0)
        rminor = kwargs.pop('rminor', 6356752.3142)
        f = (rmajor - rminor) / rmajor

        if start_point != None and end_point != None:
            distance, angle, reverse_angle = GreatCircle.vinc_dist(f, rmajor, math.radians(start_point.latitude), 
                                                                   math.radians(start_point.longitude), 
                                                                   math.radians(end_point.latitude), 
                                                                   math.radians(end_point.longitude))
        else:
            vector_dist = np.vectorize(GreatCircle.vinc_dist)
            distance, angle, reverse_angle = vector_dist(f, rmajor, np.radians(start_lat), np.radians(start_lon),
                                                         np.radians(end_lat), np.radians(end_lon))
        return {'distance': distance, 'azimuth': np.degrees(angle), 'reverse_azimuth': np.degrees(reverse_angle)}
        
        
