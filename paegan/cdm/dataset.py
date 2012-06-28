import numpy as np
import netCDF4, datetime
from timevar import Timevar
from depthvar import Depthvar
from gridvar import Gridobj

    
def CommonDataset(ncfile, xname='lon', yname='lat',
    zname='z', tname='time', **kwargs):
    """
    Initialize paegan dataset object, which uses specific
    readers for different kinds of datasets, and returns
    dataset objects that expose a common api.
    
    from cdm.dataset import CommonDataset
    >> d = Dataset()
    >> dataset = CommonDataset(ncfile)
    >> dataset = CommonDataset(url, "lon_rho", "lat_rho", "s_rho", "ocean_time")
    >> dataset = CommonDataset(url, dataset_type="cgrid") 
    """
    class self:
        pass
        
    if type(ncfile) is str:
        nc = netCDF4.Dataset(ncfile)
    self.nc = nc
    self._filename = ncfile
    self._datasettype = None
    
    if "dataset_type" in kwargs:
        self._datasettype = kwargs["dataset_type"]
    if "model" in kwargs:
        pass
    
    # Find the coordinate variables for testing, unknown
    # if not found
    #print dir(self.nc.variables)
    keys = self.nc.variables.viewkeys()
    if xname in keys and yname in keys:
        testvary = self.nc.variables[yname]
        testvarx = self.nc.variables[xname]
    elif 'lat' in keys and 'lon' in keys:
        testvary = self.nc.variables['lat']
        testvarx = self.nc.variables['lon']
    elif 'x' in keys and 'y' in keys:
        testvary = self.nc.variables['y']
        testvarx = self.nc.variables['x']
    else:
        self._datasettype = "unknown"
    
    # Test the shapes of the coordinate variables to 
    # determine the grid type
    if self._datasettype is None:
        if len(testvary.shape) > 1:
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
        
    return dataobj
        
        
class Dataset:
    def __init__(self, nc, filename, datasettype, xname='lon', yname='lat',
        zname='z', tname='time'):
        self.nc = nc
        self._filename = filename
        self._datasettype = datasettype
        self.metadata = self.nc.__dict__
        
        # Need better way to figure out depth and time names
        try:
            time_units = self.nc.variables[zname].units
        except:
            time_units = None
            
        try:
            depth_units = self.nc.variables[tname].units
        except:
            depth_units = None
            
        try:
            self._timevar = Timevar(self.nc, zname, depth_units)
        except:
            self._timevar = None
        try:
            self._depthvar = Depthvar(self.nc, tname, time_units)
        except:
            self._depthvar = None
        try:
            self._gridobj = Gridobj(self.nc, xname, yname)
        except:
            self._gridobj = None
            

    def lon2ind(self):
        pass
         
    def lat2ind(self):
        pass
            
    def ind2lon(self):
        pass
   
    def ind2lat(self):
        pass

    def gettimevar(self):
        return self._timevar

    def getdepthvar(self):
        return self._depthvar
 
    def getgridobj(self):
        return self._gridobj
 
    def getvalues(self, variable, inds=None, 
        geos=None, depths=None, times=None, bbox=None,
        timebounds=None,):
        """
        getvalues(self, variable, inds=None, 
        geos=None, depths=None, times=None, bbox=None,
        timebounds=None,)
        """
        pass
        
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
    
    def get_coords(self, var=None, **kwargs):
        assert var in self.nc.variables
        
        # If the coordinate names not in kwargs, then figure
        # out the remaining coordinate names
        if "xname" in kwargs:
            xname = kwargs["xname"]
        else:
            xname = self.nc.variables[var].coordinates.split()[-1]
            
        if "yname" in kwargs:
            yname = kwargs["yname"]
        else:
            yname = self.nc.variables[var].coordinates.split()[-2]
             
        if "zname" in kwargs:
            zname = kwargs["zname"]
        else:
            zname = self.nc.variables[var].coordinates.split()[-3]
            
        if "tname" in kwargs:
            tname = kwargs["tname"]
        else:
            tname = self.nc.variables[var].coordinates.split()[-4]
            
        
        
        
        
        
    def __repr__(self):
        s = "CommonDataset(" + self._filename + \
            ", dataset_type='" + self._datasettype + "')"
        return s
            
        
        
    _getvalues = getvalues
    _getgridobj = getgridobj
    _gettimevar = gettimevar
    _lon2ind = lon2ind
    _ind2lon = ind2lon
    _lat2ind = lat2ind
    _ind2lat = ind2lat
       
        
class CGridDataset(Dataset):
    def __new__(self, nc, filename, datasettype, xname='lon', yname='lat',
        zname='z', tname='time'):
        #self.cache = netCDF4.Dataset(cache, "w", diskless=True, persist=False)
        pass
        
    def lon2ind(self):
        pass
         
    def lat2ind(self):
        pass
            
    def ind2lon(self):
        pass
   
    def ind2lat(self):
        pass
    
    
class RGridDataset(Dataset):
    def __new__(self, nc, filename, datasettype, xname='lon', yname='lat',
        zname='z', tname='time'):
        #self.cache = netCDF4.Dataset(cache, "w", diskless=True, persist=False)
        pass
        
    def lon2ind(self):
        pass
         
    def lat2ind(self):
        pass
            
    def ind2lon(self):
        pass
   
    def ind2lat(self):
        pass
    
    
class NCellDataset(Dataset):
    def __new__(self, nc, filename, datasettype, xname='lon', yname='lat',
        zname='z', tname='time'):
        #self.cache = netCDF4.Dataset(cache, "w", diskless=True, persist=False)
        pass
        
    def lon2ind(self):
        pass
         
    def lat2ind(self):
        pass
            
    def ind2lon(self):
        pass
   
    def ind2lat(self):
        pass
        
        
