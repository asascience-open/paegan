import os
import netCDF4
from paegan.cdm.dataset import CommonDataset
from paegan.transport.location4d import Location4D

import numpy as np

class Bathymetry():
    def __init__(self, **kwargs):
        """
            Optional named arguments: 
            * file (local path or dap to bathymetry netcdf file)

        """
        
        if kwargs.get("file", None) is not None:
            self._file = os.path.normpath(kwargs.pop('file'))
        else:
            raise ValueError("Must provide a path to the Bathymetry file")
        
        self._type = kwargs.pop("type", "hover")
        self._nc = CommonDataset.open(self._file)
        self._bathy_name = kwargs.pop("bathy", "z")

    def close(self):
        self._nc.closenc()

    def intersect(self, **kwargs):
        """
            Intersect Point and Bathymetry
            returns bool
        """
        end_point = kwargs.pop('end_point')
        depth = self.get_depth(location=end_point)
        # Bathymetry and a particle's depth are both negative down
        if depth < 0 and depth > end_point.depth:
            inter = True
        else:
            inter = False
        return inter
        
    def get_depth(self, location):
        return np.mean(np.mean(self._nc.get_values(self._bathy_name, point=location)))

    def react(self, **kwargs):
        """
            The time of recation is ignored hereTime is ignored here 
            and should be handled by whatever called this function.
        """
        react_type = kwargs.get("type", self._type)

        if react_type == 'hover':
            return self.__hover(**kwargs)
        elif react_type == 'stick':
            pass
        elif react_type == 'reverse':
            return self.__reverse(**kwargs)
        else:
            raise ValueError("Bathymetry interaction type not supported")
            
    def __hover(self, **kwargs):
        """
            This hovers the particle 1m above the bathymetry WHERE IT WOULD HAVE ENDED UP.
            This is WRONG and we need to compute the location that it actually hit
            the bathymetry and hover 1m above THAT.
        """
        end_point = kwargs.pop('end_point')
        # The location argument here should be the point that intersected the bathymetry,
        # not the end_point that is "through" the bathymetry.
        depth = self.get_depth(location=end_point)
        return Location4D(latitude=end_point.latitude, longitude=end_point.longitude, depth=(depth + 1.))
        
    def __reverse(self, **kwargs):
        """
            If we hit the bathymetry, set the location to where we came from.
        """
        start_point = kwargs.pop('start_point')
        return Location4D(latitude=start_point.latitude, longitude=start_point.longitude, depth=start_point.depth)
