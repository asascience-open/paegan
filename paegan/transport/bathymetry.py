import netCDF4
from paegan.cdm.dataset import CommonDataset
from paegan.transport.location4d import Location4D

class Bathymetry():
    def __init__(self, **kwargs):
        """
            Optional named arguments: 
            * file (local path or dap to bathymetry netcdf file)

        """
        
        if "file" in kwargs:
            self._file = os.path.normpath(kwargs.pop('file'))
        else:
            self._file = os.path.normpath(os.path.join(__file__,"../../resources/bathymetry/ETOPO1_Bed_g_gmt4.grd"))
        
        self._type = kwargs.pop("type", "hover")
        self._nc = CommonDataset(self._file)
        self._bathy_name = kwargs.pop("bathy", "z")

    def intersect(self, **kwargs):
        """
            Intersect Point and Bathymetry
            returns bool
        """
        end_point = kwargs.pop('end_point')
        depth = self.get_depth(location=end_point)
        if depth > end_point.depth:
            inter = True
        else:
            inter = False
        return inter
        
    def get_depth(self, location):
        return np.mean(np.mean(self._nc.get_values(self._bathy_name, point=location)))

    def react(self, **kwargs):
    
        if self._type == 'hover':
            return self.__hover(**kwargs)
        elif self._type == 'stick':
            pass
        else:
            raise ValueError("Bathymetry interaction type not supported")
            
    def __hover(self, **kwargs):
        end_point = kwargs.pop('end_point')
        depth = np.mean(np.mean(self._nc.get_values(self._bathy_name, point=end_point)))
        return Location4D(latitude=end_point.latitude, longitude=end_point.longitude, depth=depth + 1)
        
        
