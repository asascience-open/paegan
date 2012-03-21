import math
import random
from src.external.greatcircle import GreatCircle

def genRand():
    """
    pseudo random number generator
    """
    rand = random.random()
    flip = random.random()
    if flip > 0.5:
        rand *= -1      
    return rand

class Transport:
    """
        Transport a particle in the x y and z
    """
    
    def move(self, lat, lon, depth, u, v, z, horizDisp, vertDisp, modelTimestep):
        """
        Returns the lat, lon, H, and velocity of a projected point given a starting
        lat and lon (dec deg), a depth (m) below sea surface, u, v, and z velocity components (m/s), a horizontal and vertical
        displacement coefficient (m^2/s) H (m), and a model timestep (s).

        GreatCircle calculations are done based on the Vincenty Direct method.

        Returns [ lon, lat, depth, horizontal_velocity, vertical_velocity ] as a tuple
        """

        rmajor = 6378137.0 # radius of earth's major axis (vincenty)
        rminor = 6356752.3142 # radius of earth's minor axis (vincenty)
        f = (rmajor - rminor) / rmajor # calculating flattening (vincenty)
        #f = 1 / 298.257223563 # WGS-84 ellipsoid flattening parameter (vincenty)

        u += genRand() * ((2 * horizDisp / modelTimestep) ** 0.5) # u transformation calcualtions
        v += genRand() * ((2 * horizDisp / modelTimestep) ** 0.5) # v transformation calcualtions
        z += genRand() * ((2 * vertDisp / modelTimestep) ** 0.5) # z transformation calculations

        # Move horizontally
        velocity_horiz = ((u ** 2) + (v ** 2)) ** 0.5 # calculates velocity in m/s from transformed u and v
        distance_horiz = velocity_horiz * modelTimestep # calculate the horizontal distance in meters using the velocity and model timestep
        bearing = math.atan2(u, v) # calculates the bearing resulting from vector addition of transformed u and v

        # Move vertically
        distance_vert = z * modelTimestep # calculate the vertical distance in meters using z and model timestep
        depth += distance_vert
        # Stay at the surface
        if depth < 0:
            depth = 0

        lat_result, lon_result, angle_result = GreatCircle.vinc_pt(f, rmajor, math.radians(lat), math.radians(lon), bearing, distance_horiz)

        # Convert lat and lon to degrees
        lat_result = math.degrees(lat_result)
        lon_result = math.degrees(lon_result)

        return {'lat':lat_result, 'lon':lon_result, 'reverse_angle':angle_result, 'depth':depth, 'u': u, 'v':v, 'z':z}