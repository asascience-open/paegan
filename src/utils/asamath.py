from math import sqrt, atan2, degrees

class AsaMath(object):

    @classmethod
    def speed_direction_from_u_v(cls, **kwargs):
        if "u" and "v" in kwargs:
            speed = cls.__speed_from_u_v(kwargs.get('u'), kwargs.get('v'))
            direction = cls.__direction_from_u_v(kwargs.get('u'), kwargs.get('v'), output=kwargs.get('output'))
            return { 'speed':speed, 'direction':direction }
        else:
            raise TypeError( "must pass in 'u' and 'v' values ")

    @classmethod
    def __speed_from_u_v(cls, u, v):
        return sqrt((u*u) + (v*v))

    @classmethod
    def __direction_from_u_v(cls, u, v, **kwargs):
        rads = atan2(u, v)
        if 'output' in kwargs:
            if kwargs.pop('output') == 'radians':
                return rads

        # if 'output' was not specified as 'radians', we return degrees
        if u > 0:
            return degrees(rads)
        else:
            return degrees(rads) + 360
