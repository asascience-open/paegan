import math
import unittest
from paegan.utils.asamath import AsaMath

class AsaMathTest(unittest.TestCase):
    def test_geo_angle_to_math(self):
        angle = AsaMath.azimuth_to_math_angle(azimuth=0)
        assert angle == 90

        angle = AsaMath.azimuth_to_math_angle(azimuth=45)
        assert angle == 45
        
        angle = AsaMath.azimuth_to_math_angle(azimuth=90)
        assert angle == 0

        angle = AsaMath.azimuth_to_math_angle(azimuth=180)
        assert angle == 270

        angle = AsaMath.azimuth_to_math_angle(azimuth=360)
        assert angle == 90

        angle = AsaMath.azimuth_to_math_angle(azimuth=270)
        assert angle == 180

        angle = AsaMath.azimuth_to_math_angle(azimuth=218)
        assert angle == 232

    def test_math_angle_to_geo(self):
        azimuth = AsaMath.math_angle_to_azimuth(angle=90)
        assert azimuth == 0

        azimuth = AsaMath.math_angle_to_azimuth(angle=180)
        assert azimuth == 270

        azimuth = AsaMath.math_angle_to_azimuth(angle=0)
        assert azimuth == 90

        azimuth = AsaMath.math_angle_to_azimuth(angle=360)
        assert azimuth == 90

        azimuth = AsaMath.math_angle_to_azimuth(angle=270)
        assert azimuth == 180

        azimuth = AsaMath.math_angle_to_azimuth(angle=45)
        assert azimuth == 45

        azimuth = AsaMath.math_angle_to_azimuth(angle=232)
        assert azimuth == 218

        azimuth = AsaMath.math_angle_to_azimuth(angle=45)
        assert azimuth == 45