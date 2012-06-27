import numpy as np
import netCDF4, datetime

class Dataset():
    def __init__(self, ncfile):
        """
        Initialize paegan dataset object, which uses specific
        readers for different kinds of datasets, and returns
        dataset objects that expose a common api.
        
            >> dataset = cdm.Dataset(ncfile)
        """
        self.nc = netCDF4.Dataset(ncfile)
        
        # Find the coordinate variables for testing, unknown
        # if not found
        keys = self.nc.variables.get_keys()
        if 'lat' in keys and 'lon' in keys:
            testvary = self.nc.variables['lat']
            testvarx = self.nc.variables['lon']
        elif 'x' in keys and 'y' in keys:
            testvary = self.nc.variables['y']
            testvarx = self.nc.variables['x']
        else:
            datasettype = "unknown"
        
        # Test the shapes of the coordinate variables to 
        # determine the grid type
        if datasettype != "unknown":
            if len(testvary.shape) > 1:
                datasettype = "cgrid"
            else:
                if testvary.shape[0] != testvarx.shape[0]:
                    datasettype = "rgrid"
                else:
                    datasettype = "ncell"
            
        # Return appropriate dataset subclass based on
        # datasettype
        if datasettype == 'ncell':
            dataobj = NCellDataset()
        elif datasettype == 'rgrid':
            dataobj = RGridDataset()
        elif datasettype == 'cgrid':
            dataobj = CGridDataset()
            
        return dataobj

    def lon2ind(self):
        pass
         
    def lat2ind(self):
        pass
            
    def ind2lon(self):
        pass
   
    def ind2lat(self):
        pass

    def gettimevar(self):
        pass

    def getdepthvar(self):
        pass
 
    def getgeovar(self):
        pass
 
    def getvalues(self, variable):
        pass
        
    _getvalues = getvalues
    _getgeovar = getgeovar
    _gettimevar = gettimevar
    _lon2ind = lon2ind
    _ind2lon = ind2lon
    _lat2ind = lat2ind
    _ind2lat = ind2lat
    
    
class CGridDataset(Dataset):
    pass
    
    
class RGridDataset(Dataset):
    pass
    
    
class NCellDataset(Dataset):
    pass
    
        
        
