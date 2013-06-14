from paegan.cdm.dataset import CommonDataset
import unittest, os, pytz
from datetime import datetime
import numpy as np
from shapely.geometry import Polygon, box

class DatasetTest(unittest.TestCase):

    def setUp(self):
        self.data_path = "/data/lm/tests"

    def test_rgrid_init_pws_depths(self):
        datafile = os.path.join(self.data_path, "pws_L2_2012040100.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'

        coords = pd.get_coord_dict('u')
        assert str(pd._coordcache['u']) == "[XY][Z][T]"
        names = pd.get_coord_names('u')
        assert names["tname"] == "time"
        assert names["zname"] == "depth"
        assert names["xname"] == "lon"
        assert names["yname"] == "lat"

        pd.closenc()

    def test_rgrid_init_hfradar_surface(self):
        datafile = os.path.join(self.data_path, "marcooshfradar20120331.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'

        coords = pd.get_coord_dict('u')
        assert str(pd._coordcache['u']) == "[XY][T]"
        names = pd.get_coord_names('u')
        assert names["tname"] == "time"
        assert names["zname"] == None
        assert names["xname"] == "lon"
        assert names["yname"] == "lat"

        pd.closenc()

    def test_rgrid_init_ncom_surface(self):
        datafile = os.path.join(self.data_path, "ncom_glb_sfc8_hind_2012033100.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'
        coords = pd.get_coord_dict('water_u')
        assert str(pd._coordcache['water_u']) == "[XY][T]"
        names = pd.get_coord_names('water_u')
        assert names["tname"] == "time"
        assert names["zname"] == None
        assert names["xname"] == "lon"
        assert names["yname"] == "lat"

        pd.closenc()

    def test_cgrid_init_roms_depths(self):
        datafile = os.path.join(self.data_path, "ocean_avg_synoptic_seg22.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'cgrid'

        # u grid
        coords = pd.get_coord_dict('u')
        assert str(pd._coordcache['u']) == "[XY][Z][T]"
        names = pd.get_coord_names('u')
        assert names["tname"] == "ocean_time"
        assert names["zname"] == "s_rho"
        assert names["xname"] == "lon_u"
        assert names["yname"] == "lat_u"

        # v grid
        coords = pd.get_coord_dict('v')
        assert str(pd._coordcache['v']) == "[XY][Z][T]"
        names = pd.get_coord_names('v')
        assert names["tname"] == "ocean_time"
        assert names["zname"] == "s_rho"
        assert names["xname"] == "lon_v"
        assert names["yname"] == "lat_v"

        # rho grid
        coords = pd.get_coord_dict('h')
        assert str(pd._coordcache['h']) == "[XY]"
        names = pd.get_coord_names('h')
        assert names["tname"] == None
        assert names["zname"] == None
        assert names["xname"] == "lon_rho"
        assert names["yname"] == "lat_rho"

        pd.closenc()

    def test_cgrid_init_pom_depths(self):
        datafile = os.path.join(self.data_path, "m201310100.out3.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'cgrid'

        coords = pd.get_coord_dict('u')
        assert str(pd._coordcache['u']) == "[XY][Z][T]"
        names = pd.get_coord_names('u')
        assert names["tname"] == "time"
        assert names["zname"] == "sigma"
        assert names["xname"] == "lon"
        assert names["yname"] == "lat"

        pd.closenc()

    def test_cgrid_init_slosh_surface(self):
        pass
        """
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
        names = pd.get_coord_names('eta')
        assert names["tname"] == "time"
        assert names["zname"] == None
        assert names["xname"] == "lon"
        assert names["yname"] == "lat"

        pd.closenc()
        """

    def test_ncell_init(self):
        pass
        """
        url = "http://testbedapps-dev.sura.org/thredds/dodsC/in/usf/fvcom/rita/ultralite/vardrag/nowave/3d"
        pd = CommonDataset.open(url)
        assert pd._datasettype == 'ncell'

        varname = pd.get_varname_from_stdname('sea_surface_height_above_geoid')
        assert varname == "zeta"
        names = pd.get_coord_names(varname)
        assert names["tname"] == "time"
        assert names["zname"] == None
        assert names["xname"] == "lon"
        assert names["yname"] == "lat"

        pd.closenc()
        """
        
    def test_rgrid_fluid_var_bbox(self):
        datafile = os.path.join(self.data_path, "pws_L2_2012040100.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'

        newbbox = np.asarray(pd.getbbox("u")) - 1
        test = pd.restrict_vars("u").restrict_bbox(newbbox)
        assert "v" not in set(test._current_variables)
        assert test.getbbox("u")[2] <= newbbox[2]
        assert test.getbbox("u")[3] <= newbbox[3]

        pd.closenc()

    def test_rgrid_fluid_var_bbox_time(self):
        datafile = os.path.join(self.data_path, "marcooshfradar20120331.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'

        newbbox = np.asarray(pd.getbbox("u")) - 1
        test = pd.restrict_vars("u").restrict_bbox(newbbox).nearest_time(datetime(2012,3,30,4, tzinfo=pytz.utc))
        assert "v" not in set(test._current_variables)
        assert test.getbbox("u")[2] <= newbbox[2]
        assert test.getbbox("u")[3] <= newbbox[3]
        assert test.gettimebounds("u")[0] == datetime(2012,3,30,4,0, tzinfo=pytz.utc)
        assert test.gettimebounds("u")[1] == datetime(2012,3,30,4,0, tzinfo=pytz.utc)

        pd.closenc()

    def test_bounding_polygon_rgrid(self):
        datafile = os.path.join(self.data_path, "pws_L2_2012040100.nc")
        pd = CommonDataset.open(datafile)

        bp = pd.getboundingpolygon("u")
        assert isinstance(bp, Polygon)
        bbox = pd.getbbox("u")
        shape = box(bbox[0],bbox[1],bbox[2],bbox[3])
        # Shrink some and test if within bbox
        assert bp.buffer(-0.01).within(shape)
        # Expand to encompass the bbox
        assert bp.buffer(1).contains(shape)

        pd.closenc()

    def test_bounding_polygon_roms_cgrid(self):
        datafile = os.path.join(self.data_path, "ocean_avg_synoptic_seg22.nc")
        pd = CommonDataset.open(datafile)

        bp = pd.getboundingpolygon("u")
        assert isinstance(bp, Polygon)
        bbox = pd.getbbox("u")
        shape = box(bbox[0],bbox[1],bbox[2],bbox[3])
        # Shrink some and test if within bbox
        assert bp.buffer(-0.01).within(shape)
        # Expand to encompass the bbox
        assert bp.buffer(1).contains(shape)

        """
        bp = pd.getboundingpolygon("h")
        assert isinstance(bp, Polygon)
        bbox = pd.getbbox("h")
        shape = box(bbox[0],bbox[1],bbox[2],bbox[3])
        # Shrink some and test if within bbox
        assert bp.buffer(-0.01).within(shape)
        # Expand to encompass the bbox
        assert bp.buffer(1).contains(shape)
        """

        pd.closenc()

    def test_bounding_polygon_pom_cgrid(self):
        datafile = os.path.join(self.data_path, "m201310100.out3.nc")
        pd = CommonDataset.open(datafile)

        bp = pd.getboundingpolygon("u")
        assert isinstance(bp, Polygon)
        bbox = pd.getbbox("u")
        shape = box(bbox[0],bbox[1],bbox[2],bbox[3])
        # Shrink some and test if within bbox
        assert bp.buffer(-0.01).within(shape)
        # Expand to encompass the bbox
        assert bp.buffer(1).contains(shape)

        bp = pd.getboundingpolygon("depth")
        assert isinstance(bp, Polygon)
        bbox = pd.getbbox("depth")
        shape = box(bbox[0],bbox[1],bbox[2],bbox[3])
        # Shrink some and test if within bbox
        assert bp.buffer(-0.01).within(shape)
        # Expand to encompass the bbox
        assert bp.buffer(1).contains(shape)

        pd.closenc()

    def test_bounding_polygon_ugrid(self):
        pass


    def test_bounding_polygon_ncell(self):
        pass