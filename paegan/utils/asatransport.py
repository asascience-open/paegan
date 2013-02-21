import math
from paegan.utils.asamath import AsaMath
from paegan.utils.asagreatcircle import AsaGreatCircle
from shapely.geometry import Point, Polygon, MultiPolygon
import random
import time
from datetime import timedelta

from paegan.logger import logger

class AsaTransport(object):

    @classmethod
    def get_time_objects_from_model_timesteps(cls, times, start):
        """
        Calculate the datetimes of the model timesteps

        times should start at 0 and be in seconds

        """
        modelTimestep = []
        newtimes = []

        for i in xrange(0, len(times)):
            try:
                modelTimestep.append(times[i+1] - times[i])
            except StandardError:
                modelTimestep.append(times[i] - times[i-1])
            newtimes.append(start + timedelta(seconds=times[i]))
      
        return (modelTimestep, newtimes)

    @classmethod
    def fill_polygon_with_points(cls, goal=None, polygon=None):
        """
            Fill a shapely polygon with X number of points
        """
        if goal is None:
            raise ValueError("Must specify the number of points (goal) to fill the polygon with")

        if polygon is None or (not isinstance(polygon, Polygon) and not isinstance(polygon, MultiPolygon)):
            raise ValueError("Must specify a polygon to fill points with")

        minx = polygon.bounds[0] 
        maxx = polygon.bounds[2] 
        miny = polygon.bounds[1] 
        maxy = polygon.bounds[3] 

        points = []
        now = time.time()
        while len(points) < goal:
            random_x = random.uniform(minx, maxx)
            random_y = random.uniform(miny, maxy)
            p = Point(random_x, random_y)
            if p.within(polygon):
                points.append(p)

        logger.info("Filling polygon with points took %f seconds" % (time.time() - now))

        return points

    @classmethod
    def distance_from_location_using_u_v_w(cls, u=None, v=None, w=None, timestep=None, location=None):
        """
            Calculate the greate distance from a location using u, v, and w.

            u, v, and w must be in the same units as the timestep.  Stick with seconds.

        """
        # Move horizontally
        distance_horiz = 0
        azimuth = 0
        angle = 0
        depth = location.depth

        if u is not 0 and v is not 0:
            s_and_d = AsaMath.speed_direction_from_u_v(u=u,v=v) # calculates velocity in m/s from transformed u and v
            distance_horiz = s_and_d['speed'] * timestep # calculate the horizontal distance in meters using the velocity and model timestep
            angle = s_and_d['direction']
            # Great circle calculation 
            # Calculation takes in azimuth (heading from North, so convert our mathematical angle to azimuth)
            azimuth = AsaMath.math_angle_to_azimuth(angle=angle)
            
        distance_vert = 0.
        if w is not None:
            # Move vertically
            # Depth is positive up, negative down.  w wil be negative if moving down, and positive if moving up
            distance_vert = w * timestep
            depth += distance_vert # calculate the vertical distance in meters using w (m/s) and model timestep (s)
            

        if distance_horiz != 0:
            vertical_angle = math.degrees(math.atan(distance_vert / distance_horiz))
            gc_result = AsaGreatCircle.great_circle(distance=distance_horiz, azimuth=azimuth, start_point=location) 
        else:
            # Did we go up or down?
            vertical_angle = 0.
            if distance_vert < 0:
                # Down
                vertical_angle = 270.
            elif distance_vert > 0:
                # Up
                vertical_angle = 90.
            gc_result = { 'latitude': location.latitude, 'longitude': location.longitude, 'reverse_azimuth': 0 }
            
        #logger.info("Particle moving from %fm to %fm from a vertical speed of %f m/s over %s seconds" % (location.depth, depth, w, str(timestep)))            
        gc_result['azimuth'] = azimuth
        gc_result['depth'] = depth
        gc_result['distance'] = distance_horiz
        gc_result['angle'] = angle
        gc_result['vertical_distance'] = distance_vert
        gc_result['vertical_angle'] = vertical_angle
        return gc_result