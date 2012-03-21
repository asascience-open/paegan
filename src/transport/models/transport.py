import math
import random
from src.transport.models.vincentydirect import vinc_pt

def genRand():
    """
    pseudo random number generator
    """
    rand = random.random()
    flip = random.random()
    if flip > 0.5:
        rand *= -1
    else:
        rand = rand             
    return rand

class Transport:
    """
        Transport a particle. Requires modules math, random, and from src.transport.models.vincentydirect import vinc_pt, 
        from src.transport.models.location3d import Location3D
    """
    
    def move(self, lat, lon, time, u, v, z, H, horizDisp, vertDisp, modelTimestep):
        """
        Returns the lat, lon, H, and velocity of a projected point given a starting
        lat and lon (dec deg), u, v, and z velocity components (m/s), a horizontal and vertical
        displacement constant (m), a depth, H (m), and a model timestep (s). Calculations are 
        done based on the Vincenty Direct method.

        Returns [projected lon,  projected lat, projected H, new velocity] as a Location3D object. 
        """

        rmajor = 6378137.0 # radius of earth's major axis (vincenty)
        #rminor = 6356752.3142 # radius of earth's minor axis (vincenty)
        #f = (rmajor - rminor) / rmajor # another means of calculating flattening (vincenty)
        f = 1 / 298.257223563 # WGS-84 ellipsoid flattening parameter (vincenty)

        u += genRand() * ((2 * horizDisp / modelTimestep) ** 0.5) # u transformation calcualtions
        v += genRand() * ((2 * horizDisp / modelTimestep) ** 0.5) # v transformation calcualtions
        z += genRand() * ((2 * vertDisp / modelTimestep) ** 0.5) # z transformation calculations

        velocity_horiz = ((u ** 2) + (v ** 2)) ** 0.5 # calculates velocity in m/s from transformed u and v
        bearing = math.atan2(u, v) # calculates the bearing resulting from vector addition of transformed u and v
        distance_horiz = velocity_horiz * modelTimestep # calculate the horizontal distance in meters using the velocity and model timestep
        distance_vert = z * modelTimestep # calculate the vertical distance in meters using z and model timestep

        depth = H
        lon_rad = math.radians(lon) # convert input lon to radians for the vincenty direct model
        lat_rad = math.radians(lat) # convert input lat to radians for the vincenty direct model
        lat2 = math.degrees(vinc_pt(f, rmajor, lat_rad, lon_rad, bearing, distance_horiz)[0]) # resulting lat from vincenty direct model
        lon2 = math.degrees(vinc_pt(f, rmajor, lat_rad, lon_rad, bearing, distance_horiz)[1]) # resulting lon from vincenty direct model
        depth2 = depth + distance_vert
        if depth2 < 0:
            depth2=0
        return [lon2, lat2, depth2, velocity_horiz]