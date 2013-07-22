import unittest, os, netCDF4, pytz
from datetime import timedelta, datetime, tzinfo
from paegan.cdm.depthvar import Depthvar
import numpy as np
from dateutil.parser import parse

data_path = "/data/lm/tests"

class DepthvarTest(unittest.TestCase):

    def setUp(self):
        pass 

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_conversions(self):

      datafile = os.path.join(data_path, "pws_L2_2012040100.nc")

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

