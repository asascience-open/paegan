from paegan.cdm.dataset import CommonDataset
import unittest, os, pytz
from datetime import datetime
import numpy as np

class DatasetTest(unittest.TestCase):
    def cgrid_init():
        url = "http://testbedapps-dev.sura.org/thredds/dodsC/estuarine_hypoxia/chesroms/agg-1991.nc"
        pd = CommonDataset.open(url)
        assert pd._datasettype == 'cgrid'
        coords = pd.get_coord_dict('u')
        assert str(pd._coordcache['u']) == "[XY][Z][T]"
        names = pd.get_names('u')
        assert names["tname"] == "time"
        assert names["zname"] == "s_rho"
        assert names["xname"] == "lon_u"
        assert names["yname"] == "lat_u"
        pd.closenc()

    def ncell_init():
        url = "http://testbedapps-dev.sura.org/thredds/dodsC/in/usf/fvcom/rita/ultralite/vardrag/nowave/3d"
        pd = CommonDataset.open(url)
        assert pd._datasettype == 'ncell'
        varname = pd.get_varname_from_stdname('sea_surface_height_above_geoid')
        assert varname == "zeta"
        names = pd.get_names(varname)
        assert names["tname"] == "time"
        assert names["zname"] == None
        assert names["xname"] == "lon"
        assert names["yname"] == "lat"
        pd.closenc()
 
    def slosh_test():
        url = "http://testbedapps-dev.sura.org/thredds/dodsC/in/und/slosh/ike/egl3/swi"
        pd = CommonDataset.open(url)
        assert pd._datasettype == 'cgrid'
        grid = pd.getgridobj('eta')
        box = [i-1 for i in grid.bbox]
        vals = pd.get_values('eta',
                             bbox = box, 
                             zinds = 1,
                             timeinds = 1,)
        assert vals.shape[0]==133 and vals.shape[1]==72
        names = pd.get_names('eta')
        assert names["tname"] == "time"
        assert names["zname"] == None
        assert names["xname"] == "lon"
        assert names["yname"] == "lat"
        pd.closenc()
        
    def fluid_test():
        url = "http://thredds.axiomalaska.com/thredds/dodsC/PWS_DAS.nc"
        pd = CommonDataset.open(url)
        assert pd._datasettype == 'rgrid'
        currentbbox = nc.getbbox("u")
        newbbox = np.asarray(nc.getbbox("u"))-1
        test = nc.restrict_vars("u").restrict_bbox(newbbox).restrict_depth((3, 50)).nearest_time(datetime(2011,5,1,0,0, tzinfo=pytz.utc))
        assert not "v" in set(test._current_variables)
        assert test.getbbox("u")[2] <= newbbox[2]
        assert test.getbbox("u")[3] <= newbbox[3]
        assert test.getdepthbounds("u")[0] >= 3
        assert test.getdepthbounds("u")[1] <= 50
        assert test.gettimebounds("u")[0] == datetime(2011,5,1,0,0, tzinfo=pytz.utc)
        assert test.gettimebounds("u")[1] == datetime(2011,5,1,0,0, tzinfo=pytz.utc)

