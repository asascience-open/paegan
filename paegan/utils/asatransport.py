import math
from paegan.utils.asamath import AsaMath
from paegan.utils.asagreatcircle import AsaGreatCircle

class AsaTransport(object):

    @classmethod
    def distance_from_location_using_u_v_z(cls, u=None, v=None, z=None, timestep=None, location=None):
        """
            Calculate the greate distance from a location using u, v, and z.

            u, v, and z must be in the same units as the timestep.  Stick with seconds.

        """
        # Move horizontally
        s_and_d = AsaMath.speed_direction_from_u_v(u=u,v=v) # calculates velocity in m/s from transformed u and v
        distance_horiz = s_and_d['speed'] * timestep # calculate the horizontal distance in meters using the velocity and model timestep

        # Move vertically
        distance_vert = z * timestep # calculate the vertical distance in meters using z and model timestep

        # We need to represent depths as positive up when transporting.
        depth = location.depth
        depth += distance_vert

        # Great circle calculation
        # Calculation takes in azimuth (heading from North, so convert our mathematical angle to azimuth)
        azimuth = AsaMath.math_angle_to_azimuth(angle=s_and_d['direction'])

        if distance_horiz != 0:
            vertical_angle = math.degrees(math.atan(distance_vert / distance_horiz))
        else:
            # Did we go up or down?
            vertical_angle = 0.
            if distance_vert < 1:
                vertical_angle = 270.
            elif distance_vert > 1:
                vertical_angle = 90.

        gc_result = AsaGreatCircle.great_circle(distance=distance_horiz, azimuth=azimuth, start_point=location)
        gc_result['azimuth'] = azimuth
        gc_result['depth'] = depth
        gc_result['distance'] = distance_horiz
        gc_result['angle'] = s_and_d['direction']
        gc_result['vertical_distance'] = distance_vert
        gc_result['vertical_angle'] = vertical_angle
        return gc_result