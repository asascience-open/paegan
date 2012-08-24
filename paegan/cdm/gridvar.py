import numpy as np
import netCDF4
from paegan.utils.asagreatcircle import AsaGreatCircle
from paegan.transport.location4d import Location4D

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
        return np.max(np.max(self._xarray))
        
    def get_ymax(self):
        return np.max(np.max(self._yarray))
        
    def get_xmin(self):
        return np.min(np.min(self._xarray))
        
    def get_ymin(self):
        return np.min(np.min(self._yarray))
    
    def get_bbox(self):
        self.bbox = self.xmin, self.ymin, self.xmax, self.ymax
        return self.xmin, self.ymin, self.xmax, self.ymax
            
    def get_projectedbool(self):
        return self._projected
    
    def get_xunits(self):
        try:
            units = self._nc.variables[self._xname].units
        except:
            units = None
        return units
        
    def get_yunits(self):
        try:
            units = self._nc.variables[self._yname].units
        except:
            units = None
        return units
        
    def bbox_to_wkt(self):
        pass
    
    def near_xy(self, **kwargs):
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
                inds = np.where(distance == np.min(distance))
                xinds, yinds = inds, inds
        else:
            if self._ndim == 2:
                distance = AsaGreatCircle.great_distance(
                    start_lats=self._yarray, start_lons=self._xarray,
                    end_lats=point.latitude, end_lons=point.longitude)["distance"]
                yinds, xinds = np.where(distance == np.min(distance))
            else:
                #if self._xmesh == None and self._ymesh == None:
                #    self._xmesh, self._ymesh = np.meshgrid(self._xarray, self._yarray)
                if num > 1:
                    minlat = np.abs(self._yarray - point.latitude)
                    minlon = np.abs(self._xarray - point.longitude)
                    lat_cutoff = np.sort(minlat)[num-1]
                    lon_cutoff = np.sort(minlon)[num-1]
                elif num == 1:
                    lat_cutoff = np.min(np.abs(self._yarray - point.latitude))
                    lon_cutoff = np.min(np.abs(self._xarray - point.longitude))
                yinds = np.where(np.abs(self._yarray - point.latitude) <= lat_cutoff)
                xinds = np.where(np.abs(self._xarray - point.longitude) <= lon_cutoff)

        return yinds, xinds 

        
    is_projected = property(get_projectedbool, None)
    xmax = property(get_xmax, None)
    ymax = property(get_ymax, None)
    xmin = property(get_xmin, None)
    ymin = property(get_ymin, None)
    bbox = property(get_bbox, None)
    xunits = property(get_xunits, None)
    yunits = property(get_yunits, None)
    _findy = findy
    _findx = findx
    _getxdata = getxdata
    _getydata = getydata
    
    
