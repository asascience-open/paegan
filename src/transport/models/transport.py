import math
from src.external.greatcircle import GreatCircle
from src.utils.asamath import AsaMath
from src.utils.asarandom import AsaRandom

class Transport:
    """
        Transport a particle in the x y and z direction. Requires horizontal and vertical dispersion coefficients.
        Will only move particle when self.move() is called with the proper arguments.
    """

    def __init__(self, **kwargs):

        if "horizDisp" and "vertDisp" in kwargs:
            self._horizDisp = kwargs.pop('horizDisp')
            self._vertDisp = kwargs.pop('vertDisp')
        else:
            raise TypeError( "must provide a horizontal and vertical dispersion coefficient (horizDisp and vertDisp)" )

    def set_horizDisp(self, hdisp):
        self._horizDisp = hdisp
    def get_horizDisp(self):
        return self._horizDisp
    horizDisp = property(get_horizDisp, set_horizDisp)

    def set_vertDisp(self, vdisp):
        self._vertDisp = vdisp
    def get_vertDisp(self):
        return self._vertDisp
    vertDisp = property(get_vertDisp, set_vertDisp)

    
    def move(self, location, u, v, z, modelTimestep):
        """
        Returns the lat, lon, H, and velocity of a projected point given a starting
        lat and lon (dec deg), a depth (m) below sea surface (positive up), u, v, and z velocity components (m/s), a horizontal and vertical
        displacement coefficient (m^2/s) H (m), and a model timestep (s).

        GreatCircle calculations are done based on the Vincenty Direct method.

        Returns [ lon, lat, depth, horizontal_velocity, vertical_velocity ] as a tuple
        """

        u += AsaRandom.random() * ((2 * self._horizDisp / modelTimestep) ** 0.5) # u transformation calcualtions
        v += AsaRandom.random() * ((2 * self._horizDisp / modelTimestep) ** 0.5) # v transformation calcualtions
        z += AsaRandom.random() * ((2 * self._vertDisp / modelTimestep) ** 0.5) # z transformation calculations

        # Move horizontally
        s_and_d = AsaMath.speed_direction_from_u_v(u=u,v=v) # calculates velocity in m/s from transformed u and v
        distance_horiz = s_and_d['speed'] * modelTimestep # calculate the horizontal distance in meters using the velocity and model timestep

        # Move vertically
        distance_vert = z * modelTimestep # calculate the vertical distance in meters using z and model timestep
        depth = location.depth
        depth += distance_vert
        # Stay at the surface
        if depth > 0:
            depth = 0

        # Great circle calculation
        result = self.great_circle(distance=distance_horiz, angle=s_and_d['direction'], start_point=location)

        # Convert lat and lon to degrees
        lat_result = math.degrees(result['latitude'])
        lon_result = math.degrees(result['longitude'])
        angle_result = result['reverse_angle']

        return {'lat':lat_result, 'lon':lon_result, 'reverse_angle':angle_result, 'depth':depth, 'u': u, 'v':v, 'z':z, 'distance':distance_horiz, 'angle': s_and_d['direction'], 'vertical_distance':distance_vert}

    def great_circle(self, **kwargs):
        """
            Named arguments:
            distance = distance to traveled
            angle = angle to travel in
            start_point = Location4D object representing the starting point
            rmajor = radius of earth's major axis. default=6378137.0 (WGS84)
            rminor = radius of earth's minor axis. default=6356752.3142 (WGS84)
        """

        distance = kwargs.pop('distance')
        angle = kwargs.pop('angle')
        starting = kwargs.pop('start_point')
        rmajor = kwargs.pop('rmajor', 6378137.0)
        rminor = kwargs.pop('rminor', 6356752.3142)
        f = (rmajor - rminor) / rmajor

        lat_result, lon_result, angle_result = GreatCircle.vinc_pt(f, rmajor, math.radians(starting.latitude), math.radians(starting.longitude), angle, distance)        

        return {'latitude': lat_result, 'longitude': lon_result, 'reverse_angle': angle_result}

    def __str__(self):
        return  " *** Transport *** " + \
                "\nhorizDisp: " + str(self.horizDisp) + \
                "\nvertDisp: " + str(self.vertDisp)

