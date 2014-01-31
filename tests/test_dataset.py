from paegan.cdm.dataset import CommonDataset
import unittest, os, pytz
from datetime import datetime
import numpy as np
from shapely.geometry import Polygon, box

data_path = "/data/lm/tests"

class DatasetTest(unittest.TestCase):

    def setUp(self):
        pass

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_rgrid_init_pws_depths(self):

        datafile = os.path.join(data_path, "pws_L2_2012040100.nc")
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

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "marcooshfradar20120331.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_rgrid_init_hfradar_surface(self):

        datafile = os.path.join(data_path, "marcooshfradar20120331.nc")
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

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "ncom_glb_sfc8_hind_2012033100.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_rgrid_init_ncom_surface(self):

        datafile = os.path.join(data_path, "ncom_glb_sfc8_hind_2012033100.nc")
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

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_cgrid_init_roms_depths(self):

        datafile = os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")
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

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "m201310100.out3.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_cgrid_init_pom_depths(self):

        datafile = os.path.join(data_path, "m201310100.out3.nc")
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

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_rgrid_fluid_var_bbox(self):

        datafile = os.path.join(data_path, "pws_L2_2012040100.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'

        newbbox = np.asarray(pd.getbbox("u")) - 1
        test = pd.restrict_vars("u").restrict_bbox(newbbox)
        assert "v" not in set(test._current_variables)
        assert test.getbbox("u")[2] <= newbbox[2]
        assert test.getbbox("u")[3] <= newbbox[3]

        pd.closenc()

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "marcooshfradar20120331.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_rgrid_fluid_var_bbox_time(self):

        datafile = os.path.join(data_path, "marcooshfradar20120331.nc")
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

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_bounding_polygon_rgrid(self):

        datafile = os.path.join(data_path, "pws_L2_2012040100.nc")
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

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_bounding_polygon_roms_cgrid(self):

        datafile = os.path.join(data_path, "ocean_avg_synoptic_seg22.nc")
        pd = CommonDataset.open(datafile)

        bp = pd.getboundingpolygon("u")
        assert isinstance(bp, Polygon)
        bbox = pd.getbbox("u")
        shape = box(bbox[0],bbox[1],bbox[2],bbox[3])
        # Shrink some and test if within bbox
        assert bp.buffer(-0.01).within(shape)

        bp = pd.getboundingpolygon("h")
        assert isinstance(bp, Polygon)
        bbox = pd.getbbox("h")
        shape = box(bbox[0],bbox[1],bbox[2],bbox[3])
        # Shrink some and test if within bbox
        assert bp.buffer(-0.01).within(shape)

        pd.closenc()

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "m201310100.out3.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_bounding_polygon_pom_cgrid(self):

        datafile = os.path.join(data_path, "m201310100.out3.nc")
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

    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_rgrid_regrid_4d(self):
        from paegan.utils.asainterpolate import create_grid
        datafile = os.path.join(data_path, "pws_L2_2012040100.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'
        var = "u"
        lon = [-148.25, -148.24, -148.23, -148.22, -148.21, -148.2, -148.19, -148.18, -148.17, -148.16, -148.15, -148.14, -148.13, -148.12, -148.11, -148.1, -148.09, -148.08, -148.07, -148.06, -148.05, -148.04, -148.03, -148.02, -148.01, -148.0, -147.99, -147.98, -147.97, -147.96, -147.95, -147.94, -147.93, -147.92, -147.91, -147.9, -147.89, -147.88, -147.87, -147.86, -147.85, -147.84, -147.83, -147.82, -147.81, -147.8, -147.79, -147.78, -147.77, -147.76, -147.75, -147.74, -147.73, -147.72, -147.71, -147.7, -147.69, -147.68, -147.67, -147.66, -147.65, -147.64, -147.63, -147.62, -147.61, -147.6, -147.59, -147.58, -147.57, -147.56, -147.55, -147.54, -147.53, -147.52, -147.51, -147.5, -147.49, -147.48, -147.47, -147.46, -147.45, -147.44, -147.43, -147.42, -147.41, -147.4, -147.39, -147.38, -147.37, -147.36, -147.35, -147.34, -147.33, -147.32, -147.31, -147.3, -147.29, -147.28, -147.27, -147.26, -147.25, -147.24, -147.23, -147.22, -147.21, -147.2, -147.19, -147.18, -147.17, -147.16, -147.15, -147.14, -147.13, -147.12, -147.11, -147.1, -147.09, -147.08, -147.07, -147.06, -147.05, -147.04, -147.03, -147.02, -147.01, -147.0, -146.99, -146.98, -146.97, -146.96, -146.95, -146.94, -146.93, -146.92, -146.91, -146.9, -146.89, -146.88, -146.87, -146.86, -146.85, -146.84, -146.83, -146.82, -146.81, -146.8, -146.79, -146.78, -146.77, -146.76, -146.75, -146.74, -146.73, -146.72, -146.71, -146.7, -146.69, -146.68, -146.67, -146.66, -146.65, -146.64, -146.63, -146.62, -146.61, -146.6, -146.59, -146.58, -146.57, -146.56, -146.55, -146.54, -146.53, -146.52, -146.51, -146.5, -146.49, -146.48, -146.47, -146.46, -146.45, -146.44, -146.43, -146.42, -146.41, -146.4, -146.39, -146.38, -146.37, -146.36, -146.35, -146.34, -146.33, -146.32, -146.31, -146.3, -146.29, -146.28, -146.27, -146.26, -146.25, -146.24, -146.23, -146.22, -146.21, -146.2, -146.19, -146.18, -146.17, -146.16, -146.15, -146.14, -146.13, -146.12, -146.11, -146.1, -146.09, -146.08, -146.07, -146.06, -146.05, -146.04, -146.03, -146.02, -146.01, -146.0, -145.99, -145.98, -145.97, -145.96, -145.95, -145.94, -145.93, -145.92, -145.91, -145.9, -145.89, -145.88, -145.87, -145.86, -145.85, -145.84, -145.83, -145.82, -145.81, -145.8, -145.79, -145.78, -145.77, -145.76, -145.75, -145.74, -145.73, -145.72, -145.71, -145.7, -145.69, -145.68, -145.67, -145.66, -145.65, -145.64, -145.63, -145.62, -145.61, -145.6, -145.59, -145.58, -145.57, -145.56, -145.55, -145.54, -145.53, -145.52, -145.51, -145.5, -145.49, -145.48, -145.47, -145.46, -145.45, -145.44, -145.43, -145.42, -145.41, -145.4, -145.39, -145.38, -145.37, -145.36, -145.35, -145.34, -145.33, -145.32, -145.31, -145.3, -145.29, -145.28, -145.27, -145.26, -145.25, -145.24, -145.23, -145.22, -145.21, -145.2, -145.19, -145.18, -145.17, -145.16, -145.15, -145.14, -145.13, -145.12, -145.11, -145.1, -145.09, -145.08, -145.07, -145.06, -145.05, -145.04, -145.03, -145.02, -145.01, -145.0, -144.99, -144.98, -144.97, -144.96, -144.95, -144.94, -144.93, -144.92, -144.91, -144.9, -144.89, -144.88, -144.87, -144.86, -144.85, -144.84, -144.83, -144.82, -144.81, -144.8, -144.79]
        lat = [59.68, 59.69, 59.7, 59.71, 59.72, 59.73, 59.74, 59.75, 59.760002, 59.77, 59.78, 59.79, 59.8, 59.81, 59.82, 59.83, 59.84, 59.85, 59.86, 59.87, 59.88, 59.89, 59.9, 59.91, 59.920002, 59.93, 59.94, 59.95, 59.96, 59.97, 59.98, 59.99, 60.0, 60.010002, 60.02, 60.03, 60.04, 60.05, 60.06, 60.07, 60.08, 60.09, 60.1, 60.11, 60.12, 60.13, 60.14, 60.15, 60.16, 60.170002, 60.18, 60.19, 60.2, 60.21, 60.22, 60.23, 60.24, 60.25, 60.260002, 60.27, 60.28, 60.29, 60.3, 60.31, 60.32, 60.33, 60.34, 60.35, 60.36, 60.37, 60.38, 60.39, 60.4, 60.41, 60.420002, 60.43, 60.44, 60.45, 60.46, 60.47, 60.48, 60.49, 60.5, 60.510002, 60.52, 60.53, 60.54, 60.55, 60.56, 60.57, 60.58, 60.59, 60.6, 60.61, 60.62, 60.63, 60.64, 60.65, 60.66, 60.670002, 60.68, 60.69, 60.7, 60.71, 60.72, 60.73, 60.74, 60.75, 60.760002, 60.77, 60.78, 60.79, 60.8, 60.81, 60.82, 60.83, 60.84, 60.85, 60.86, 60.87, 60.88, 60.89, 60.9, 60.91, 60.920002, 60.93, 60.94, 60.95, 60.96, 60.97, 60.98, 60.99, 61.0, 61.010002, 61.02, 61.03, 61.04, 61.05, 61.06, 61.07, 61.08, 61.09, 61.1, 61.11, 61.12, 61.13, 61.14, 61.15, 61.16, 61.170002, 61.18, 61.19, 61.2]
        lon, lat = np.asarray(lon), np.asarray(lat)
        data1 = pd.get_values(var, bbox = (-149, 59, -144, 61.5))
        coords_struct = pd.sub_coords(var, bbox = (-149, 59, -144, 61.5))
        data2 = pd.get_values_on_grid(var, coords_struct.x, coords_struct.y, t=coords_struct.time, z=coords_struct.z)

        pd.closenc()
        assert np.all(data1 == data2)


    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_L2_2012040100.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_rgrid_get_values(self):
        datafile = os.path.join(data_path, "pws_L2_2012040100.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'
        values = pd.get_values(var="u", bbox=[-149, 59, -144, 61.5], timeinds=0)
        assert values.size > 0


    @unittest.skipIf(not os.path.exists(os.path.join(data_path, "pws_das_2014012600.nc")),
                     "Resource files are missing that are required to perform the tests.")
    def test_aggregated_dataset(self):
        datafile = os.path.join(data_path, "pws_das_20140126*.nc")
        pd = CommonDataset.open(datafile)
        assert pd._datasettype == 'rgrid'
        values = pd.get_values(var="u", bbox=[-149, 59, -144, 61.5], timeinds=0)
        assert values.size > 0
