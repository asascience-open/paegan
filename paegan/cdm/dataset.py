import numpy as np
import netCDF4, datetime
from timevar import Timevar
from depthvar import Depthvar
from gridvar import Gridobj
from variable import Coordinates as cachevar
from variable import SubCoordinates as subs

_possiblet = ["time", "TIME", "Time",
           "t", "T",
           "ocean_time", "OCEAN_TIME",
           "jd", "JD",
           "dn", "DN",
           "times", "TIMES", "Times",
           "mt", "MT",
           "dt", "DT",
          ]
_possiblez = ["depth", "DEPTH",
           "depths", "DEPTHS",
           "height", "HEIGHT",
           "altitude", "ALTITUDE",
           "alt", "ALT", 
           "Alt", "Altitude",
           "h", "H",
           "s_rho", "S_RHO",
           "s_w", "S_W",
           "z", "Z",
           "siglay", "SIGLAY",
           "siglev", "SIGLEV",
          ]
_possiblex = ["x", "X",
           "lon", "LON",
           "xlon", "XLON",
           "lonx", "lonx",
           "lon_u", "LON_U",
           "lon_v", "LON_V",
           "lonc", "LONC",
           "Lon", "Longitude",
           "longitude", "LONGITUDE",
           "lon_rho", "LON_RHO",
           "lon_psi", "LON_PSI",
          ]
_possibley = ["y", "Y",
           "lat", "LAT",
           "ylat", "YLAT",
           "laty", "laty",
           "lat_u", "LAT_U",
           "lat_v", "LAT_V",
           "latc", "LATC",
           "Lat", "Latitude",
           "latitude", "LATITUDE",
           "lat_rho", "LAT_RHO",
           "lat_psi", "LAT_PSI",
          ]
    
def CommonDataset(ncfile, xname='lon', yname='lat',
    zname='z', tname='time', **kwargs):
    """
    Initialize paegan dataset object, which uses specific
    readers for different kinds of datasets, and returns
    dataset objects that expose a common api.
    
    from cdm.dataset import CommonDataset

    >> dataset = CommonDataset(ncfile)
    >> dataset = CommonDataset(url, "lon_rho", "lat_rho", "s_rho", "ocean_time")
    >> dataset = CommonDataset(url, dataset_type="cgrid")
    """
    class self:
        pass
        
    if isinstance(ncfile, str):
        ncfile = unicode(ncfile)

    if isinstance(ncfile, unicode):
        nc = netCDF4.Dataset(ncfile)

    self.nc = nc
    self._filename = ncfile
    self._datasettype = kwargs.get('dataset_type', None)
    if kwargs.get('model', None) != None:
        pass
    
    # Find the coordinate variables for testing, unknown
    # if not found
    #print dir(self.nc.variables)
    keys = self.nc.variables
    keys = set(keys)
    posx = set(_possiblex)
    posy = set(_possibley)
    xmatches = list(posx.intersection(keys))
    ymatches = list(posy.intersection(keys))
    
    if xname in keys and yname in keys:
        testvary = self.nc.variables[yname]
        testvarx = self.nc.variables[xname]
    elif len(xmatches) > 0:
        testvary = self.nc.variables[ymatches[0]]
        testvarx = self.nc.variables[xmatches[0]]
    
    # Test the shapes of the coordinate variables to 
    # determine the grid type
    if self._datasettype is None:
        if testvary.ndim > 1:
            self._datasettype = "cgrid"
        else:
            if testvary.shape[0] != testvarx.shape[0]:
                self._datasettype = "rgrid"
            else:
                self._datasettype = "ncell"
    
    # Return appropriate dataset subclass based on
    # datasettype
    if self._datasettype == 'ncell':
        dataobj = NCellDataset(self.nc, 
            self._filename, self._datasettype,
            zname=zname, tname=tname, xname=xname, yname=yname)
    elif self._datasettype == 'rgrid':
        dataobj = RGridDataset(self.nc,
            self._filename, self._datasettype,
            zname=zname, tname=tname, xname=xname, yname=yname)
    elif self._datasettype == 'cgrid':
        dataobj = CGridDataset(self.nc,
            self._filename, self._datasettype,
            zname=zname, tname=tname, xname=xname, yname=yname)
    else:
        dataobj = None
    return dataobj
    

class Dataset:
    def __init__(self, nc, filename, datasettype, xname='lon', yname='lat',
        zname='z', tname='time'):
        self.nc = nc
        self._coordcache = dict()
        self._filename = filename
        self._datasettype = datasettype
        self.metadata = self.nc.__dict__
        
        self._possiblet = _possiblet
        self._possiblez = _possiblez
        self._possiblex = _possiblex
        self._possibley = _possibley
                
        if xname not in self._possiblex:
            self._possiblex.append(xname)
        if yname not in self._possibley:
            self._possibley.append(yname)
        if zname not in self._possiblez:
            self._possiblez.append(zname)
        if tname not in self._possiblet:
            self._possiblet.append(tname)
            
    def getvariableinfo(self):
        variables = {}
        for var in self.nc.variables.keys():
            variables[var] = {}
            for attr in self.nc.variables[var].ncattrs():
                variables[var][attr] = self.nc.variables[var].getncattr(attr)
        return variables
                           
    def lon2ind(self, var=None, **kwargs):
        pass
         
    def lat2ind(self, var=None, **kwargs):
        pass
            
    def ind2lon(self, var=None, **kwargs):
        pass
   
    def ind2lat(self, var=None, **kwargs):
        pass
        
    def closenc(self):
        self.metadata = None
        self.nc.close()
        self.nc = None
        
    def opennc(self):
        self.nc = netCDF4.Dataset(self._filename)
        self.metadata = self.nc.__dict__
    
    def gettimestep(self, var=None):
        assert var in self.nc.variables
        time = self.gettimevar(var)
        return time.timestep
    
    def gettimebounds(self, var=None, **kwargs):
        assert var in self.nc.variables
        time = self.gettimevar(var)
        if "units" in kwargs:
            bounds = (netCDF4.num2date(np.min(time),units=u),
                      netCDF4.num2date(np.max(time),units=u))
        else:
            bounds = (np.min(time.dates), np.max(time.dates))
        return bounds

    def getdepthbounds(self, var=None, **kwargs):
        assert var in self.nc.variables
        depths = self.getdepthvar(var)
        if "units" in kwargs:
            if kwargs["units"] == "m":
                bounds = (np.min(depths.get_m), np.max(depths.get_m))
            else:
                bounds = ()
        else:
            bounds = (np.min(time), np.max(time))
        return bounds
    
    def getbbox(self, var=None, **kwargs):
        assert var in self.nc.variables
        grid = self.getgridobj(var)
        return grid.bbox
        
    def getboundingpolygon(self, var=None, **kwargs):
        assert var in self.nc.variables
        # TODO: This should return a bounding polygon of the dataset
        return self.getbbox(var)
        
    def _checkcache(self, var):
        assert var in self.nc.variables
        test = var in self._coordcache
        return test

    def gettimevar(self, var=None, use_cache=True):
        #return self._timevar
        assert var in self.nc.variables
        timevar = None
        if use_cache == True:
            if self._checkcache(var):
                timevar = self._coordcache[var].time
            else:
                self._coordcache[var] = cachevar()
        if timevar == None:
            names = self.get_coord_names(var)
            if names['tname'] != None:
                timevar = Timevar(self.nc, names["tname"])
            else:
                timevar = None
            if use_cache == True:  
                self._coordcache[var].time = timevar
        return timevar
 
    def getdepthvar(self, var=None, use_cache=True):
        #return self._depthvar
        assert var in self.nc.variables
        depthvar = None
        if use_cache == True:
            if self._checkcache(var):
                depthvar = self._coordcache[var].z
            else:
                self._coordcache[var] = cachevar()
        if depthvar == None:
            names = self.get_coord_names(var)
            if names['zname'] != None:
                depthvar = Depthvar(self.nc, names["zname"])
            else:
                depthvar = None
            if use_cache == True:
                self._coordcache[var].add_z(depthvar)
        return depthvar
        
    def getgridobj(self, var=None):
        #return self._gridobj
        assert var in self.nc.variables
        gridobj = None
        if self._checkcache(var):
            gridobj = self._coordcache[var].xy
        else:
            self._coordcache[var] = cachevar()
        if gridobj == None:
            names = self.get_coord_names(var)
            if names['xname'] != None or names['yname'] !=None:
                gridobj = Gridobj(self.nc, names["xname"], 
                   names["yname"])
            else:
                gridobj = None
            self._coordcache[var].add_xy(gridobj)
        return gridobj
        
    def get_tind_from_bounds(self, var, bounds, convert=False, use_cache=True):
        assert var in self.nc.variables
        time = self.gettimevar(var, use_cache)
        if convert:
            bounds = netCDF4.date2num(bounds, time._units + " since " + time.origin.isoformat())
        inds = np.where(np.logical_and(time.dates >= bounds[0].replace(tzinfo=time.dates[0].tzinfo), time.dates <= bounds[1].replace(tzinfo=time.dates[0].tzinfo)))
        return inds
    
    def get_zind_from_bounds(self, var, bounds, use_cache=True):
        assert var in self.nc.variables
        depths = self.getdepthvar(var, use_cache)
        inds = np.where(np.logical_and(depths >= bounds[0], depths <= bounds[1]))
        return inds
        
    def get_nearest_tind(self, var, point, use_cache=True):
        assert var in self.nc.variables
        time = self.gettimevar(var, use_cache)
        return time.nearest_index(point.time)
        
    def get_nearest_zind(self, var, point, use_cache=True):
        assert var in self.nc.variables
        depths = self.getdepthvar(var, use_cache)
        return depths.nearest_index(point.depth)
        
    def __str__(self):
        k = []
        for key in self.nc.variables.viewkeys():
            k.append(key)
        out = """
[[ 
  <Paegan Dataset Object>
  Dataset Type: """ + self._datasettype + """ 
  Resource: """ + self._filename + """
  Variables: 
  """ + str(k) + """
]]"""
        return out 
    
    def get_coord_names(self, var=None, **kwargs):
        assert var in self.nc.variables
        ncvar = self.nc.variables[var]
        try:
            coordinates = ncvar.coordinates.split()
        except:
            coordinates = []
        # If the coordinate names not in kwargs, then figure
        # out the remaining coordinate names
        if "xname" in kwargs:
            xname = kwargs["xname"]
        else:
            xname = list(set(coordinates) & set(self._possiblex))
            if len(xname) > 0:
                xname = xname[0]
            else:
                xname = None
        if "yname" in kwargs:
            yname = kwargs["yname"]
        else:
            yname = list(set(coordinates) & set(self._possibley))
            if len(yname) > 0:
                yname = yname[0]
            else:
                yname = None
        if "zname" in kwargs:
            zname = kwargs["zname"]
        else:
            zname = list(set(coordinates) & set(self._possiblez))
            if len(zname) > 0:
                zname = zname[0]
            else:
                zname = None
        if "tname" in kwargs:
            tname = kwargs["tname"]
        else:
            tname = list(set(coordinates) & set(self._possiblet))
            if len(tname) > 0:
                tname = tname[0]
            else:
                tname = None      
        names = {"tname":tname, "zname":zname,
                 "xname":xname, "yname":yname}
        # find how the shapes match up to var
        # (should i use dim names or just sizes to figure out?)
        # I'm going to use dim names
        dims = ncvar.dimensions
        ndim = ncvar.ndim
        shape = ncvar.shape
        total = []
        for i in names:
            name = names[i]
            if name != None:
                cdims = self.nc.variables[name].dimensions
                for cdim in cdims:
                    try:
                        total.append(dims.index(cdim))
                    except:
                        pass 
        total = np.unique(np.asarray(total))

        for missing in range(ndim):
            if missing not in total:

                missing_dim = dims[missing]

                if missing_dim in self.nc.variables:
                    if missing_dim in self._possiblex:
                        name2 = "xname"
                    elif missing_dim in self._possibley:
                        name2 = "yname"
                    elif missing_dim in self._possiblez:
                        name2 = "zname"
                    elif missing_dim in self._possiblet:
                        name2 = "tname"
                    else:
                        name2 = None
                    if name2 != None:
                        names[name2] = missing_dim
        # Need to add next check if there are any dims left
        # to find variables with different names that use soley
        # those dims and appear in our type keys
        
        # then make guesses based on attributes like:
        # units, standard_name, perhaps time attribute, axis 
        # attribute (X,Y,Z,T),
        
        # then...
        return names
              
    def get_coord_dict(self, var=None, **kwargs):
        assert var in self.nc.variables
        timevar = self.gettimevar(var)
        depthvar = self.getdepthvar(var)
        gridobj = self.getgridobj(var)
        return {"time":timevar, "z":depthvar, "xy":gridobj}
        
        
    def get_varname_from_stdname(self, standard_name=None,
        match=None):
        var_matches = []
        if match == None:
            for var in self.nc.variables:
                try:
                    sn = self.nc.variables[var].standard_name
                    if standard_name == sn:
                        var_matches.append(var)
                except:
                    pass
        else:
            pass
        return var_matches
        
    def __repr__(self):
        s = "CommonDataset(" + self._filename + \
            ", dataset_type='" + self._datasettype + "')"
        return s
        
    def sub_coords(self, var, zbounds=None, bbox=None,
        timebounds=None, zinds=None, timeinds=None):
        assert var in self.nc.variables
        coord_dict = self.get_coord_dict(var)
        names = self.get_coord_names(var)
        x, y, z, time = None, None, None, None
        if names['tname'] != None:
            #tname = names['tname']
            if timebounds != None:
                timeinds = self.get_tind_from_bounds(var, timebounds)
            time = coord_dict['time'][timeinds[0]:timeinds[-1]+1]
        if names['zname'] != None:
            #zname = names['zname']
            if zbounds != None:
                zinds = self.get_zind_from_bounds(var, zbounds)
            z = coord_dict['z'][zinds[0]:zinds[-1]+1]
        xinds, yinds = self.get_xyind_from_bbox(var, bbox)
        xy = coord_dict['xy']
        if names['xname'] != None:
            #xname = names['xname']
            if len(xy._xarray.shape) == 2:
                x = xy._xarray[xinds[0][0]:xinds[0][-1]+1, xinds[1][0]:xinds[1][-1]+1]
            elif len(xy.xarray.shape) == 1:
                x = xy._xarray[np.squeeze(xinds)]
        if names['yname'] != None:
            #yname = names['yname']
            if len(xy._yarray.shape) == 2:
                y = xy._yarray[yinds[0][0]:yinds[0][-1]+1, yinds[1][0]:yinds[1][-1]+1]
            elif len(xy.yarray.shape) == 1:
                y = xy._yarray[np.squeeze(yinds)]
        return subs(x=x, y=y, z=z, time=time)
        
    def get_indices(self, var, zbounds=None, bbox=None,
        timebounds=None, zinds=None, timeinds=None, 
        point=None, use_local=False, **kwargs):
        """
        
        Get smallest chunck of data that encompasses the 4-d
        bounding box limits of the data completely.
        
        
        """
        assert var in self.nc.variables
        ncvar = self.nc.variables[var]
        names = self.get_coord_names(var)
        # find how the shapes match up to var
        # (should i use dim names or just sizes to figure out?)
        # I'm going to use dim names
        dims = ncvar.dimensions
        ndim = ncvar.ndim
        shape = ncvar.shape
        positions = dict()
        total = []
        for i in names:
            name = names[i]
            if i == "tname":
                common_name = "time"
            elif i == "zname":
                common_name = "z"
            elif i == "xname":
                common_name = "x"
            elif i == "yname":
                common_name = "y"
            else:
                common_name = None
            if common_name != None:
                positions[common_name] = None
                if name != None:
                    positions[common_name] = []
                    cdims = self.nc.variables[name].dimensions
                    for cdim in cdims:
                        try:
                            positions[common_name].append(dims.index(cdim))
                        except:
                            pass

        if positions["time"] != None:
            if timebounds != None:
                tinds = self.get_tind_from_bounds(var, timebounds)
            else:
                if timeinds == None:
                    if point != None:
                        tinds = np.asarray([self.get_nearest_tind(var, point)])
                    else:
                        tinds = np.arange(0, ncvar.shape[positions["time"]]+1)
                else:
                    tinds = timeinds
        if positions["z"] != None:
            if zbounds != None:
                zinds = self.get_zind_from_bounds(var, zbounds)
            else:
                if zinds == None:
                    if point != None:
                        zinds = np.asarray([self.get_nearest_zind(var, point)])
                    else:
                        zinds = np.arange(0, ncvar.shape[positions["z"]]+1)
                else:
                    pass
        if bbox != None:
            xinds, yinds = self.get_xyind_from_bbox(var, bbox)
        else:
            if point != None:
                num = kwargs.get("num", 1)
                xinds, yinds = self.get_xyind_from_point(var, point, num=num)
            else:
                xinds = [np.arange(0, ncvar.shape[pos]+1) for pos in positions["x"]]
                yinds = [np.arange(0, ncvar.shape[pos]+1) for pos in positions["y"]]

        indices = [None for i in range(ndim)]
        for name in positions:
            if positions[name] != None:
                if name == "time":
                    for i,position in enumerate(positions[name]):
                        indices[position] = tinds[i] 
                elif name == "z":
                    for i,position in enumerate(positions[name]):
                        indices[position] = zinds[i]
                elif name == "y":
                    for i,position in enumerate(positions[name]):
                        indices[position] = yinds[i]
                elif name == "x":
                    for i,position in enumerate(positions[name]):
                        indices[position] = xinds[i]
        
        return indices
    
    def get_values(self, var, zbounds=None, bbox=None,
        timebounds=None, zinds=None, timeinds=None, 
        point=None, use_local=False, **kwargs):
        """
        
        Get smallest chunck of data that encompasses the 4-d
        bounding box limits of the data completely.
        
        
        """
        assert var in self.nc.variables
        ncvar = self.nc.variables[var]
        names = self.get_coord_names(var)
        # find how the shapes match up to var
        # (should i use dim names or just sizes to figure out?)
        # I'm going to use dim names
        dims = ncvar.dimensions
        ndim = ncvar.ndim
        shape = ncvar.shape
        positions = dict()
        total = []
        for i in names:
            name = names[i]
            if i == "tname":
                common_name = "time"
            elif i == "zname":
                common_name = "z"
            elif i == "xname":
                common_name = "x"
            elif i == "yname":
                common_name = "y"
            else:
                common_name = None
            if common_name != None:
                positions[common_name] = None
                if name != None:
                    positions[common_name] = []
                    cdims = self.nc.variables[name].dimensions
                    for cdim in cdims:
                        try:
                            positions[common_name].append(dims.index(cdim))
                        except:
                            pass
        # get t inds, z inds, xy inds
        # tinds = [[1,],]
        # zinds = [[1,],]
        # xinds = [[50,], [50,]]
        # yinds = [[50,], [50,]]
        if positions["time"] != None:
            if timebounds != None:
                tinds = self.get_tind_from_bounds(var, timebounds)
            else:
                if timeinds == None:
                    if point != None:
                        tinds = np.asarray([self.get_nearest_tind(var, point)])
                    else:
                        tinds = np.arange(0, ncvar.shape[positions["time"]]+1)
                else:
                    tinds = timeinds
        if positions["z"] != None:
            if zbounds != None:
                zinds = self.get_zind_from_bounds(var, zbounds)
            else:
                if zinds == None:
                    if point != None:
                        zinds = np.asarray([self.get_nearest_zind(var, point)])
                    else:
                        zinds = np.arange(0, ncvar.shape[positions["z"]]+1)
                else:
                    pass
        if bbox != None:
            xinds, yinds = self.get_xyind_from_bbox(var, bbox)
        else:
            if point != None:
                num = kwargs.get("num", 1)
                xinds, yinds = self.get_xyind_from_point(var, point, num=num)
            else:
                xinds = [np.arange(0, ncvar.shape[pos]+1) for pos in positions["x"]]
                yinds = [np.arange(0, ncvar.shape[pos]+1) for pos in positions["y"]]
        #if len(tinds) > 0 and len(zinds) > 0 and \
        #    len(xinds) > 0 and len(yinds) > 0:
        # Now take time inds, z inds, x and y inds and put them 
        # into the request in the right places:
       
        indices = [None for i in range(ndim)]
        for name in positions:
            if positions[name] != None:
                if name == "time":
                    for i,position in enumerate(positions[name]):
                        indices[position] = tinds[i] 
                elif name == "z":
                    for i,position in enumerate(positions[name]):
                        indices[position] = zinds[i]
                elif name == "y":
                    for i,position in enumerate(positions[name]):
                        indices[position] = yinds[i]
                elif name == "x":
                    for i,position in enumerate(positions[name]):
                        indices[position] = xinds[i]
        
        if np.all([i.size >0 for i in indices]):
            data = self._get_data(var, indices, use_local)
        else:
            # data = None
            raise ValueError("no data inside the domian specified")
        return data
        
    def _get_data(self, var, **kwargs):
        pass
                
    _get_values = get_values
    _getgridobj = getgridobj
    _gettimevar = gettimevar
    _getdepthvar = getdepthvar
    _lon2ind = lon2ind
    _ind2lon = ind2lon
    _lat2ind = lat2ind
    _ind2lat = ind2lat
    __get_data = _get_data
        
        
        
        
class CGridDataset(Dataset):
    """
    CGridDataset(Dataset)
    """
    def __new__(self, nc, filename, datasettype, xname='lon', yname='lat',
        zname='z', tname='time'):
        pass

    def lon2ind(self, var=None, **kwargs):
        pass
         
    def lat2ind(self, var=None, **kwargs):
        pass
            
    def ind2lon(self, var=None, **kwargs):
        pass
   
    def ind2lat(self, var=None, **kwargs):
        pass
        
    def get_xyind_from_bbox(self, var, bbox, **kwargs):
 
        grid = self.getgridobj(var)
        xbool = grid.get_xbool_from_bbox(bbox)
        ybool = grid.get_ybool_from_bbox(bbox)
        inds = np.where(np.logical_and(xbool, ybool))
        minrow = np.min(inds[0])
        mincol = np.min(inds[1])
        maxrow = np.max(inds[0])
        maxcol = np.max(inds[1])
        inds = (np.arange(minrow, maxrow+1), np.arange(mincol, maxcol+1))
        return inds, inds #xinds, yinds
    
    def get_xyind_from_point(self, var, point, **kwargs):
        grid = self.getgridobj(var)
        num = kwargs.get("num", None)
        indexr, indexc = grid.near_xy(point=point, num=num)
        inds = indexc, indexr
        return inds, inds
        

    def _get_data(self, var, indarray, use_local=False):
        ndims = len(indarray)
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
        
        
        
        
class RGridDataset(Dataset):
    """
    RGridDataset(Dataset)
    """
    def __new__(self, nc, filename, datasettype, xname='lon', yname='lat',
        zname='z', tname='time'):
        pass
        
    def lon2ind(self, var=None, **kwargs):
        pass
         
    def lat2ind(self, var=None, **kwargs):
        pass
            
    def ind2lon(self, var=None, **kwargs):
        pass
   
    def ind2lat(self, var=None, **kwargs):
        pass
        
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




class NCellDataset(Dataset):
    """
    NCellDataset(Dataset)
    """
    def __new__(self, nc, filename, datasettype, xname='lon', yname='lat',
        zname='z', tname='time'):
        pass
        if None in self.nc.variables:
            self._is_topology = True
            self.topology_var_name = None
        
    def lon2ind(self, var=None, **kwargs):
        pass
         
    def lat2ind(self, var=None, **kwargs):
        pass
            
    def ind2lon(self, var=None, **kwargs):
        pass
   
    def ind2lat(self, var=None, **kwargs):
        pass
        
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
        
        
        
