import unittest, os, netCDF4, pytz
from datetime import timedelta, datetime, tzinfo
from paegan.cdm.timevar import Timevar
import numpy as np
from dateutil.parser import parse

data_path = "/data/lm/tests"

class TimevarTest(unittest.TestCase):

    def setUp(self):
        pass

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")) or \
                     not os.path.exists(os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_timevar_length(self):
        datafile = os.path.join(data_path, "pws_L2_2012040100.nc")
        # Manually extract
        ds = netCDF4.Dataset(datafile)
        data = ds.variables['time'][:]
        # Timevar extract
        tvar = Timevar(datafile)
        assert data.shape == tvar.shape

        datafile = os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")
        # Manually extract
        ds = netCDF4.Dataset(datafile)
        data = ds.variables['ocean_time'][:]
        # Timevar extract
        tvar = Timevar(datafile, name='ocean_time')
        assert data.shape == tvar.shape

        ds.close()

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")) or \
                     not os.path.exists(os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_timevar_roms_seconds_values(self):

        datafile = os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")

        # Manually extract
        # ocean_time:units = "seconds since 1990-01-01 00:00:00" ;
        # ocean_time:calendar = "gregorian" ;
        dt = datetime(1990,1,1, tzinfo=pytz.utc)
        ds = netCDF4.Dataset(datafile)
        data = ds.variables['ocean_time'][:]
        # Convert to days
        factor = 60 * 60 * 24
        data = data / factor

        # Timevar extract
        tvar = Timevar(datafile, name='ocean_time')

        assert np.allclose(data,tvar.days)

        # Now compare datetimes
        data = data.tolist()
        jds = []
        for x in data:
            jds.append(dt + timedelta(days=x))

        assert (jds == tvar.dates).all()

        ds.close()

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")) or \
                     not os.path.exists(os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_timevar_hfradar_days_values(self):

        datafile = os.path.join(data_path, "marcooshfradar20120331.nc")

        # Manually extract
        # time:units = days since 2001-01-01 00:00:00
        dt = datetime(2001,1,1, tzinfo=pytz.utc)
        ds = netCDF4.Dataset(datafile)
        data = ds.variables['time'][:]

        # Timevar extract
        tvar = Timevar(datafile, name='time', tzinfo=pytz.utc)

        assert np.allclose(data,tvar.days)

        # Now compare datetimes
        data = data.tolist()
        jds = []
        for x in data:
            jds.append(dt + timedelta(days=x))

        assert (jds == tvar.dates).all()

        ds.close()

    def test_timevar_ncom_hour_values_dap(self):

        datafile = "http://edac-dap3.northerngulfinstitute.org/thredds/dodsC/US_East/ncom_relo_useast_u_2011080200/ncom_relo_useast_u_2011080200_t072.nc"

        # Manually extract
        # time:units = hour since 2000-01-01 00:00:00
        dt = datetime(2000,1,1, tzinfo=pytz.utc)
        ds = netCDF4.Dataset(datafile)
        data = ds.variables['time'][:]
        # Convert to days
        factor = 24
        data = data / factor

        # Timevar extract
        tvar = Timevar(datafile, name='time', tzinfo=pytz.utc)

        assert np.allclose(data,tvar.days)

        # Now compare datetimes
        data = data.tolist()
        jds = []
        for x in data:
            jds.append(dt + timedelta(days=x))

        assert (jds == tvar.dates).all()

        ds.close()
