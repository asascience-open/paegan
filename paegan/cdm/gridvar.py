import numpy as np
import netCDF4
from paegan.utils.asagreatcircle import AsaGreatCircle
from paegan.location4d import Location4D
from shapely.geometry import MultiLineString, LineString
from shapely.ops import polygonize

class Gridobj:
    def __init__(self, nc, xname=None, yname=None,
        xunits=None, yunits=None, projected=False, **kwargs):
        self._projected = projected
        if type(nc) is str:
            nc = netCDF4.Dataset(nc)

        self._nc = nc
        self._xname = xname
        self._yname = yname
        self._ndim = self._nc.variables[self._xname].ndim
        self._ymesh = None
        self._xmesh = None
        self._type = None

        if self._xname != None:
            self._x_nc = self._nc.variables[self._xname]
            self._xarray = np.asarray(self._x_nc[:])
            if self.xmax <= 360 and self.xmin >= 0:
                self._xarray[np.where(self._xarray > 180)] = \
                    self._xarray[np.where(self._xarray > 180)] - 360

        else:
            self._xarray = np.asarray((),)
        if self._yname !=None:
            self._y_nc = self._nc.variables[self._yname]
            self._yarray = np.asarray(self._y_nc[:])
        else:
            self._yarray = np.asarray((),)


    def get_xbool_from_bbox(self, bbox):
        return np.logical_and(self._xarray<=bbox[2],
                              self._xarray>=bbox[0])

    def get_ybool_from_bbox(self, bbox):
        return np.logical_and(self._yarray<=bbox[3],
                              self._yarray>=bbox[1])

    def getydata(self):
        pass

    def getxdata(self):
        pass

    def findx(self):
        pass

    def findy(self):
        pass

    def get_xmax(self):
        return np.nanmax(np.nanmax(self._xarray))

    def get_ymax(self):
        return np.nanmax(np.nanmax(self._yarray))

    def get_xmin(self):
        return np.nanmin(np.nanmin(self._xarray))

    def get_ymin(self):
        return np.nanmin(np.nanmin(self._yarray))

    def get_bbox(self):
        """
            TODO: Implement ncell bbox
        """
        if self._ndim == 2:
            xtmp = self._xarray[np.isnan(self._xarray)==False]
            bbox = np.nanmin(self._xarray[:,0]), self.ymin, np.nanmax(self._xarray[:,-1]), self.ymax
        else:
            xtmp = self._xarray[np.isnan(self._xarray)==False]
            bbox = xtmp[0], self.ymin, xtmp[-1], self.ymax
        return bbox

    def get_boundingpolygon(self):
        """
            TODO: Implement ncell bbox

            order of lines creation (assumes 0,0 is x)
            -----3-----
            |         |
            4         2
            |         |
            x----1-----
        """

        if self._ndim == 2: # CGRID
            nx,ny = self._xarray.shape
            one = MultiLineString([((self._xarray[i][0],self._yarray[i][0]),(self._xarray[i+1][0],self._yarray[i+1][0])) for i in range(nx-1)])
            two = MultiLineString([((self._xarray[nx-1][j],self._yarray[nx-1][j]),(self._xarray[nx-1][j+1],self._yarray[nx-1][j+1])) for j in range(ny-1)])
            three = MultiLineString([((self._xarray[i][ny-1],self._yarray[i][ny-1]),(self._xarray[i-1][ny-1],self._yarray[i-1][ny-1])) for i in reversed(range(1,nx))])
            four = MultiLineString([((self._xarray[0][j],self._yarray[0][j]),(self._xarray[0][j-1],self._yarray[0][j-1])) for j in reversed(range(1,ny))])
            m = one.union(two).union(three).union(four)
        else: # RGRID
            nx,ny = self._xarray.shape[0], self._yarray.shape[0]
            one = LineString([(self._xarray[i], self._yarray[0]) for i in range(nx)])
            two = LineString([(self._xarray[-1], self._yarray[i]) for i in range(ny)])
            three = LineString([(self._xarray[i], self._yarray[-1]) for i in reversed(range(nx))])
            four = LineString([(self._xarray[0], self._yarray[i]) for i in reversed(range(ny))])
            m = MultiLineString([one,two,three,four])

        polygons = list(polygonize(m))
        # -- polygonize returns a list of polygons, including interior features, the largest in area "should" be the full feature
        polygon = sorted(polygons, key=lambda x: x.area)[-1]
        return polygon

    def get_projectedbool(self):
        return self._projected

    def get_xunits(self):
        try:
            units = self._nc.variables[self._xname].units
        except StandardError:
            units = None
        return units

    def get_yunits(self):
        try:
            units = self._nc.variables[self._yname].units
        except StandardError:
            units = None
        return units

    def bbox_to_wkt(self):
        pass

    def near_xy(self, **kwargs):
        """
            TODO: Implement ncell near_xy
        """
        point = kwargs.get("point", None)
        if point == None:
            lat = kwargs.get("lat", None)
            lon = kwargs.get("lon", None)
            point = Location4D(latitude=lat, longitude=lon)
        num = kwargs.get("num", 1)
        ncell = kwargs.get("ncell", False)
        if ncell:
            if num > 1:
                pass
            else:
                distance = AsaGreatCircle.great_distance(
                    start_lats=self._yarray, start_lons=self._xarray,
                    end_lats=point.latitude, end_lons=point.longitude)["distance"]
                inds = np.where(distance == np.nanmin(distance))
                xinds, yinds = inds, inds
        else:
            if self._ndim == 2:
                distance = AsaGreatCircle.great_distance(
                    start_lats=self._yarray, start_lons=self._xarray,
                    end_lats=point.latitude, end_lons=point.longitude)["distance"]
                yinds, xinds = np.where(distance == np.nanmin(distance))
            else:
                #if self._xmesh == None and self._ymesh == None:
                #    self._xmesh, self._ymesh = np.meshgrid(self._xarray, self._yarray)
                if num > 1:
                    minlat = np.abs(self._yarray - point.latitude)
                    minlon = np.abs(self._xarray - point.longitude)
                    lat_cutoff = np.sort(minlat)[num-1]
                    lon_cutoff = np.sort(minlon)[num-1]
                elif num == 1:
                    lat_cutoff = np.nanmin(np.abs(self._yarray - point.latitude))
                    lon_cutoff = np.nanmin(np.abs(self._xarray - point.longitude))
                yinds = np.where(np.abs(self._yarray - point.latitude) <= lat_cutoff)
                xinds = np.where(np.abs(self._xarray - point.longitude) <= lon_cutoff)

        return yinds, xinds


    is_projected = property(get_projectedbool, None)
    xmax = property(get_xmax, None)
    ymax = property(get_ymax, None)
    xmin = property(get_xmin, None)
    ymin = property(get_ymin, None)
    bbox = property(get_bbox, None)
    boundingpolygon = property(get_boundingpolygon, None)
    xunits = property(get_xunits, None)
    yunits = property(get_yunits, None)
    _findy = findy
    _findx = findx
    _getxdata = getxdata
    _getydata = getydata


