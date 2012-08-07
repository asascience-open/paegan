from math import sqrt, atan2, degrees, radians

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
        rads = atan2(v, u)
        if 'output' in kwargs:
            if kwargs.pop('output') == 'radians':
                return rads

        # if 'output' was not specified as 'radians', we return degrees
        return cls.normalize_angle(angle=degrees(rads))

    @classmethod
    def azimuth_to_math_angle(cls, **kwargs):
        return cls.normalize_angle(angle=90 - kwargs.get("azimuth"))

    @classmethod
    def math_angle_to_azimuth(cls, **kwargs):
        return cls.normalize_angle(angle=(360 - kwargs.get("angle")) + 90)

    @classmethod
    def normalize_angle(cls, **kwargs):
        return kwargs.get('angle') % 360

    @classmethod
    def is_number(cls, num):
        try:
            float(num) # for int, long and float
        except TypeError:
            try:
                complex(num) # for complex
            except TypeError:
                return False

        return True
