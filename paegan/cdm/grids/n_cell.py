import copy

import numpy as np

from paegan.cdm.dataset import Dataset, _sub_by_nan


class NCellDataset(Dataset):
    """

        NCellDataset(Dataset)

    """
    def __init__(self, *args,**kwargs):
        super(NCellDataset,self).__init__(*args, **kwargs)
        if None in self.nc.variables:
            self._is_topology = True
            self.topology_var_name = None

    def _copy(self):
        new = NCellDataset(self._filepath, self._datasettype)
        new._coordcache = copy.copy(self._coordcache)
        new._current_variables = copy.copy(self._current_variables)
        return new

    def restrict_bbox(self, bbox = None, **kwargs):
        assert bbox != None
        assert len(bbox) == 4
        new = self._copy()
        for var in new._current_variables:
            grid = new.getgridobj(var)
            if grid != None:
                inds, inds =  new.get_xyind_from_bbox(var, bbox)
                grid._xarray = _sub_by_nan(grid._xarray, inds[0][0])
                grid._yarray = _sub_by_nan(grid._yarray, inds[0][0])
                new._coordcache[var].xy = grid
        return new

    def nearest_point(self, point):
        assert type(point) == Location4D
        new = self._copy()
        for var in new._current_variables:
            grid = new.getgridobj(var)
            if grid != None:
                inds, inds = new.get_xyind_from_point(var, point)
                grid._xarray = _sub_by_nan(grid._xarray, inds)
                grid._yarray = _sub_by_nan(grid._yarray, inds)
                new._coordcache[var].xy = grid
        return new

    def get_xyind_from_bbox(self, var, bbox):
        grid = self.getgridobj(var)
        xbool = grid.get_xbool_from_bbox(bbox)
        ybool = grid.get_ybool_from_bbox(bbox)
        inds = np.where(np.logical_and(xbool, ybool))
        return inds, inds #xinds, yinds

    def get_xyind_from_point(self, var, point, **kwargs):
        num = kwargs.get("num", 1)
        grid = self.getgridobj(var)
        inds, inds = grid.near_xy(point=point, num=num, ncell=True)
        return inds, inds

    def _get_data(self, var, indarray, use_local=False):
        ndims = len(indarray)
        if use_local == False:
            var =    self.nc.variables[var]
        else:
            pass
        if ndims == 1:
            data = var[:]
            data = data[indarray]
        elif ndims == 2:
            data = var[:]
            data = data[indarray[0], indarray[1]]
        elif ndims == 3:
            data = var[indarray[0], indarray[1], :]
            data = data[:, :, indarray[2]]
        elif ndims == 4:
            data = var[indarray[0], indarray[1], indarray[2],
                       indarray[3]]
        elif ndims == 5:
            data = var[indarray[0], indarray[1], indarray[2],
                       indarray[3], indarray[4]]
        elif ndims == 6:
            data = var[indarray[0], indarray[1], indarray[2],
                       indarray[3], indarray[4], indarray[5]]
        return data
