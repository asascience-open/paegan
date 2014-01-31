import copy

import numpy as np

from paegan.cdm.dataset import Dataset, _sub_by_nan


class RGridDataset(Dataset):
    """

        RGridDataset(Dataset)

    """
    def __init__(self, *args,**kwargs):
        super(RGridDataset,self).__init__(*args, **kwargs)

    def _copy(self):
        new = RGridDataset(self._filepath, self._datasettype)
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
                xinds, yinds =  new.get_xyind_from_bbox(var, bbox)
                grid._xarray = _sub_by_nan(grid._xarray, xinds[0][0])
                grid._yarray = _sub_by_nan(grid._yarray, yinds[0][0])
                new._coordcache[var].xy = grid
        return new

    def nearest_point(self, point):
        assert type(point) == Location4D
        new = self._copy()
        for var in new._current_variables:
            grid = new.getgridobj(var)
            if grid != None:
                xind, yind = new.get_xyind_from_point(var, point)
                grid._xarray = _sub_by_nan(grid._xarray, xind)
                grid._yarray = _sub_by_nan(grid._yarray, yind)
                new._coordcache[var].xy = grid
        return new

    def get_xyind_from_bbox(self, var, bbox):
        grid = self.getgridobj(var)
        xbool = grid.get_xbool_from_bbox(bbox)
        ybool = grid.get_ybool_from_bbox(bbox)
        xinds = [np.where(xbool)]
        yinds = [np.where(ybool)]
        return xinds, yinds #xinds, yinds

    def get_xyind_from_point(self, var, point, **kwargs):
        grid = self.getgridobj(var)
        num = kwargs.get("num", 1)
        index = grid.near_xy(point=point, num=num)
        return index[1], index[0]

    def _get_data(self, var, indarray, use_local=False):
        ndims = len(indarray)
        #print "this is what im trying to get", indarray
        if use_local == False:
            var = self.nc.variables[var]
        else:
            pass

        if ndims == 1:
            data = var[indarray]
        elif ndims == 2:
            data = var[indarray[0], indarray[1]]
        elif ndims == 3:
            data = var[indarray[0], indarray[1], indarray[2]]
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
