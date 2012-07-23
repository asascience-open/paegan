import netCDF4
from paegan.cdm.dataset import CommonDataset

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
        #nc = CommonDataset(self._file)
        
        

    def intersect(self, **kwargs):
        """
            Intersect a Line or Point Collection and the Bathymetry
        """
        ls = None
        if "linestring" in kwargs:
            ls = kwargs.pop('linestring')
        elif "start_point" and "end_point" in kwargs:
            ls = LineString(list(kwargs.pop('start_point').coords) + list(kwargs.pop('end_point').coords))
        else:
            raise TypeError( "must provide a LineString geometry object or (2) Point geometry objects" )
        
        inter = False
        return inter
        
    def react(self, **kwargs):
    
        if self._type == 'hover':
            pass
        elif self._type == 'stick':
            pass
        else:
            raise ValueError("Bathymetry interaction type not supported")
        
        
