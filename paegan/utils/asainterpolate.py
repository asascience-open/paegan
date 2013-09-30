import numpy as np
from scipy.interpolate import griddata

def create_grid(lonmin, lonmax, latmin, latmax, **kwargs):
    dx, dy = kwargs.get("dx", None), kwargs.get("dy", None)
    nx, ny = kwargs.get("nx", None), kwargs.get("ny", None)
    if nx==None or ny==None:
        if dx==None or dy==None:
            raise KeyError("Please kwargs dx and dy to define the interval between grid points, or nx and ny to define the number of grid points (include endpoints) between the bbox limits")
        else:
            nx, ny = (lonmax-lonmin)/dx, (latmax-latmin)/dy
    lat_grid = np.linspace(latmin, latmax, ny, endpoint=True)
    lon_grid = np.linspace(lonmin, lonmax, nx, endpoint=True)
    return lon_grid, lat_grid

class GenInterpolator(object):
    def __init__(self, data, *dimensions, **kwargs):
        for dim in dimensions:
            assert len(dim.shape) == 1
        method = kwargs.get('method', 'nearest')
        dimensions = [dim.flatten() for dim in dimensions]
        points = [dim.flatten() for dim in np.meshgrid(*dimensions)]
        points = np.asarray(points).T
        self.points = points
        self.data = data.flatten()
        self.method = method
        self.numdim = len(dimensions)

    def interpgrid(self, *dimensions):
        if len(dimensions) != self.numdim:
            raise ValueError("Please interpolate data to the same number of dimensions as source data.")
        else:
            for dim in dimensions:
                assert len(dim.shape) == 1
            flatdims = [dim.flatten() for dim in dimensions]
            newpoints = [dim.flatten() for dim in np.meshgrid(*flatdims)]
            newpoints = np.asarray(newpoints).T
            f = griddata(self.points, self.data, newpoints, method=self.method)
            unique = []
            for dim in dimensions:
                unique.append(dim.shape[0])
            return np.squeeze( f.reshape( *unique ) )

class CfGeoInterpolator(object):
    def __init__(self, data, lon, lat, t=None, z=None, **kwargs):
        method = kwargs.get('method', 'nearest')
        coords = {'lat':lat, 'lon':lon, 'z':z, 't':t}
        dimensions, ndshape = self._flatten_coords(**coords)
        self.points = np.asarray(dimensions).T
        self.data = data.flatten()
        self.method = method
        self.numdim = self.points.shape[1]
        assert self.data.shape[0] == self.points.shape[0]

    def interpgrid(self, lon, lat, t=None, z=None, **kwargs):
        coords = {'lat':lat, 'lon':lon, 'z':z, 't':t}
        dimensions, ndshape = self._flatten_coords(**coords)
        dimensions = np.asarray(dimensions).T
        #print self.points.shape, self.data.shape, dimensions.shape
        #print np.histogram(self.data)
        f = griddata(self.points, self.data, dimensions, method=self.method)
        return np.squeeze( f.reshape( *ndshape ) )

    def _flatten_coords(self, **coords):
        lat = coords.get('lat', None)
        lon = coords.get('lon', None)
        z = coords.get('z', None)
        t = coords.get('t', None)
        ndshape = []

        # Configure latitude and longitude to produce vectors of cell by
        # cell coordinates
        if len(lat.shape) == 2:
            assert np.all(lat.shape==lon.shape)
            ndshape.append(lat.shape[1])
            ndshape.append(lat.shape[0])
            latshape = lat.shape
            lat = lat.flatten()
            lon = lon.flatten()
        else:
            assert len(lat.shape) == 1
            assert len(lon.shape) == 1
            ndshape.append(lon.shape[0])
            ndshape.append(lat.shape[0])
            lon, lat = np.meshgrid(lon, lat, indexing='ij')
            latshape = lat.shape
            lon = lon.flatten()
            lat = lat.flatten()

        # Configure the z coords to provide cell by cell z value
        if z == None:
            if t == None:
                dimensions = [lon, lat]
            else:
                ndshape.append(t.shape[0])
                lat = np.meshgrid(t, lat, indexing='ij')[-1]
                t, lon = np.meshgrid(t, lon, indexing='ij')
                dimensions = [lon.flatten(), lat.flatten(), t.flatten()]
        elif len(z.shape) == 4:
            assert t != None
            ndshape.append(z.shape[1])
            ndshape.append(t.shape[0])
            lat = np.meshgrid(t, range(z.shape[1]), lat, indexing='ij')[-1]
            t, dummy, lon = np.meshgrid(t, range(z.shape[1]), lon, indexing='ij')
            z = z.flatten()
            dimensions = [lon.flatten(), lat.flatten(), z, t.flatten()]
        elif len(z.shape) ==  3:
            assert np.all(z.shape[1:] == latshape)
            if t == None:
                ndshape.append(z.shape[0])
                lat = np.meshgrid(range(z.shape[0]), lat, indexing='ij')[-1]
                lon = np.meshgrid(range(z.shape[0]), lon, indexing='ij')[-1]
                z = z.flatten()
                dimensions = [lon.flatten(), lat.flatten(), z]
            else:
                ndshape.append(z.shape[0])
                ndshape.append(t.shape[0])
                lat = np.meshgrid(t, range(z.shape[0]), lat, indexing='ij')[-1]
                lon = np.meshgrid(t, range(z.shape[0]), lon, indexing='ij')[-1]
                t, z = np.meshgrid(t, z.flatten(), indexing='ij')
                dimensions = [lon.flatten(), lat.flatten(), z.flatten(), t.flatten()]
        elif len(z.shape) == 1:
            if t == None:
                ndshape.append(z.shape[0])
                lat = np.meshgrid(z, lat, indexing='ij')[-1]
                z, lon = np.meshgrid(z, lon, indexing='ij')
                dimensions = [lon.flatten(), lat.flatten(), z.flatten()]
            else:
                ndshape.append(z.shape[0])
                ndshape.append(t.shape[0])
                lat = np.meshgrid(t, z, lat, indexing='ij')[-1]
                t, z, lon = np.meshgrid(t, z, lon, indexing='ij')
                dimensions = [lon.flatten(), lat.flatten(), z.flatten(), t.flatten()]

        return dimensions, ndshape[::-1]
