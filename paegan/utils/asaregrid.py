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

class Interpolator(object):
    def __init__(self, *dimensions, **kwargs):
        dimensions = [dim.flatten() for dim in dimensions]
        points = [dim.flatten() for dim in np.meshgrid(*dimensions)]
        points = np.asarray(points).T
        self.points = points
        self.data = data.flatten()
        self.method = kwargs.get('method', 'nearest')
        self.numdim = len(dimensions)

    def interpgrid(self, *dimensions):
        if len(dimensions) != self.numdim:
            raise ValueError("Please interpolate data to the same number of dimensions as source data.")
        else:
            flatdims = [dim.flatten() for dim in dimensions]
            newpoints = [dim.flatten() for dim in np.meshgrid(*flatdims)]
            newpoints = np.asarray(newpoints).T
            f = griddata(self.points, self.data, newpoints, method=self.method)
            unique = []
            for dim in dimensions:
                unique.append(dim.shape)
            unique = np.asarray(unique).unique()
            return np.squeeze( f.reshape( *unique ) )

