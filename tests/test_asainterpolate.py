import math
import unittest
import numpy as np
from paegan.utils.asainterpolate import GenInterpolator, CfGeoInterpolator, create_grid

class CfInterpolator(unittest.TestCase):
    def test_interpolator_2d(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        data = np.random.rand(50, 50)
        i = CfGeoInterpolator(data, lon, lat, method='nearest')
        data2 = i.interpgrid(lon, lat)
        assert np.all(data==data2)
        
    def test_interpolator_2dmesh(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        lon, lat = np.meshgrid(lon, lat, indexing='ij')
        data = np.random.rand(50, 50)
        i = CfGeoInterpolator(data, lon, lat, method='nearest')
        data2 = i.interpgrid(lon, lat)
        assert np.all(data==data2)
        
    def test_interpolator_3d_1dz_2dll(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        z = np.arange(10)
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        lon, lat = np.meshgrid(lon, lat, indexing='ij')
        data = np.random.rand(10, 50, 50)
        i = CfGeoInterpolator(data, lon, lat, z=z, method='nearest')
        data2 = i.interpgrid(lon, lat, z=z)
        assert np.all(data==data2)
        
    def test_interpolator_3d_3dz_2dll(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        z, dummy, dummy2 = np.meshgrid(np.arange(10), lon, lat, indexing='ij')
        lon, lat = np.meshgrid(lon, lat)
        data = np.random.rand(10, 50, 50)
        i = CfGeoInterpolator(data, lon, lat, z=z, method='nearest')
        data2 = i.interpgrid(lon, lat, z=z)
        assert np.all(data==data2)
        
    def test_interpolator_3d_1dz_1dll(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        data = np.random.rand(10, 50, 50)
        z = np.arange(10)
        i = CfGeoInterpolator(data, lon, lat, z=z, method='nearest')
        data2 = i.interpgrid(lon, lat, z=z)
        assert np.all(data==data2)
        
    def test_interpolator_3d_3dz_1dll(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        data = np.random.rand(10, 50, 50)
        z, dummy, dummy2 = np.meshgrid(np.arange(10), lon, lat, indexing='ij')
        i = CfGeoInterpolator(data, lon, lat, z=z, method='nearest')
        data2 = i.interpgrid(lon, lat, z=z)
        assert np.all(data==data2)
        
    def test_interpolator_3d_1dt_3dz_1dll(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        data = np.random.rand(9, 10, 50, 50)
        z, dummy, dummy2 = np.meshgrid(np.arange(10), lon, lat, indexing='ij')
        t = np.arange(9)
        i = CfGeoInterpolator(data, lon, lat, z=z, t=t, method='nearest')
        data2 = i.interpgrid(lon, lat, z=z, t=t)
        assert np.all(data==data2)
        
    def test_interpolator_3d_1dt_1dz_1dll(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        data = np.random.rand(9, 10, 50, 50)
        z = np.arange(10)
        t = np.arange(9)
        i = CfGeoInterpolator(data, lon, lat, z=z, t=t, method='nearest')
        data2 = i.interpgrid(lon, lat, z=z, t=t)
        assert np.all(data==data2)
        
    def test_interpolator_3d_1dt_4dz_1dll(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        data = np.random.rand(9, 10, 50, 50)
        t = np.arange(9)
        dumm3, z, dummy, dummy2 = np.meshgrid(t, np.arange(10), lon, lat, indexing='ij')
        i = CfGeoInterpolator(data, lon, lat, z=z, t=t, method='nearest')
        data2 = i.interpgrid(lon, lat, z=z, t=t)
        assert np.all(data==data2)
        
class GeneralInterpolator(unittest.TestCase):
    def test_interpolator_2d(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        data = np.random.rand(50, 50)
        i = GenInterpolator(data, lat, lon, method='nearest')
        data2 = i.interpgrid(lat, lon)
        assert np.all(data==data2)
        
class AsaCreateGrid(unittest.TestCase):
    def test_create_grid(self):
        lonbounds = [-70, -60]
        latbounds = [40, 50]
        nx, ny = 50, 50
        lon, lat = create_grid(lonbounds[0], lonbounds[1], latbounds[0], latbounds[1], nx=50, ny=50)
        assert lon[0] == lonbounds[0]
        assert lon[-1] == lonbounds[1]
        assert lat[0] == latbounds[0]
        assert lat[-1] == latbounds[1]
        assert lon.shape[0] == nx
        assert lat.shape[0] == ny
        
