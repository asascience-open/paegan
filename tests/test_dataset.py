from paegan.cdm.dataset import CommonDataset
import unittest
import os

class DatasetTest(unittest.TestCase):
    def cgrid_init():
        url = "http://testbedapps-dev.sura.org/thredds/dodsC/estuarine_hypoxia/chesroms/agg-1991.nc"
        pd = CommonDataset(url)
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
        pd = CommonDataset(url)
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
        pd = CommonDataset(url)
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

