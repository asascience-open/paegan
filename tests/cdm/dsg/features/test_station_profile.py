# -*- coding: utf-8 -*-
import unittest
from datetime import datetime

from shapely.geometry import Point as sPoint

from paegan.cdm.dsg.member import Member
from paegan.cdm.dsg.features.station_profile import StationProfile
from paegan.cdm.dsg.features.base.point import Point
from paegan.cdm.dsg.features.base.profile import Profile

class StationProfileTest(unittest.TestCase):
    def test_station_profile(self):

        sp = StationProfile()
        sp.name = "Profile Station"
        sp.location = sPoint(-77, 33)
        sp.uid = "1234"
        sp.set_property("authority", "IOOS")

        # add a sequence of profiles
        for y in xrange(3):
            dt1 = datetime(2013, 1, 1, 12, 0, 10 * y)
            prof1          = Profile()
            prof1.location = sPoint(-77, 33)
            prof1.time     = dt1

            # add a string of points going down in z
            for x in xrange(5):
                p1 = Point()
                p1.time = dt1
                p1.location = sPoint(-77, 33, -5 * x)

                member1 = Member(value=30 - (2 * x), units='°C', name='Water Temperature', description='water temperature', standard='sea_water_temperature')
                member2 = Member(value=80 + (2 * x), units='PSU', name='Salinity', description='salinity', standard='salinity')
                p1.add_member(member1)
                p1.add_member(member2)

                prof1.add_element(p1)

            sp.add_element(prof1)

        sp.calculate_bounds()

        assert sp.size == 3
        assert len(sp.time_range) == 3

        assert sp.depth_range[0] == -20
        assert sp.depth_range[-1] == 0

        assert sp.get_property("authority") == "IOOS"
        assert sp.uid == "1234"

        assert len(sp.get_unique_members()) == 2


