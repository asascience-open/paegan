import unittest
import os
import netCDF4
from datetime import timedelta, datetime, tzinfo
from paegan.cdm.depthvar import Depthvar
import numpy as np
from dateutil.parser import parse
import pytz

class DepthvarTest(unittest.TestCase):

    def setUp(self):
        self.data_path = "/data/lm/tests"

    def test_conversions(self):

        datafile = os.path.join(self.data_path, "pws_L2_2012040100.nc")

        # Manually extract
        ds = netCDF4.Dataset(datafile)
        data = ds.variables['depth'][:]

        # Depthvar extract
        dvar = Depthvar(datafile, 'depth')

        assert data.all() == dvar.all()

        kilo = dvar.kilometers
        assert ((data * 0.001) == kilo).all()

        cents = dvar.centimeters
        assert ((data * 100) == cents).all()