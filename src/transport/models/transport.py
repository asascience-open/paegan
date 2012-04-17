import math
from src.utils.asamath import AsaMath
from src.utils.asarandom import AsaRandom
from src.utils.asagreatcircle import AsaGreatCircle

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

        # We need to represent depths as positive up when transporting.
        depth = location.depth
        depth += distance_vert

        # vertical angle
        vertical_angle = math.degrees(math.atan(distance_vert / distance_horiz))

        # Great circle calculation
        # Calculation takes in azimuth (heading from North, so convert our mathematical angle to azimuth)
        azimuth = AsaMath.math_angle_to_azimuth(angle=s_and_d['direction'])
        result = AsaGreatCircle.great_circle(distance=distance_horiz, azimuth=azimuth, start_point=location)

        return {'latitude':result['latitude'], 'azimuth': azimuth, 'reverse_azimuth': result['reverse_azimuth'], 'longitude':result['longitude'], 'depth':depth, 'u': u, 'v':v, 'z':z, 'distance':distance_horiz, 'angle': s_and_d['direction'], 'vertical_distance':distance_vert, 'vertical_angle':vertical_angle}

    def __str__(self):
        return  " *** Transport *** " + \
                "\nhorizDisp: " + str(self.horizDisp) + \
                "\nvertDisp: " + str(self.vertDisp)

