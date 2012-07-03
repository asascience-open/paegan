import numpy as np

class Coordinates:
    """
    This is just a container to hold the coordinate variables persistently in the dataset obj for each of the field variables of interest.
    """
    def __init__(self, **kwargs):
        self.xy, self.z, self.time = None, None, None
    
        if "gridobj" in kwargs:
            self.xy = kwargs["xy"]
        if "depthvar" in kwargs:
            self.z = kwargs["z"]
        if "timevar" in kwargs:
            self.time = kwargs["time"]
            
    def add_xy(self, gridobj):
        self.xy = gridobj
        
    def add_z(self, depthvar):
        self.z = depthvar
        
    def add_time(self, timevar):
       self.time = timevar
    
    def _getinfo(self):
       info = ""
       if self.xy != None:
           info = info + "[XY]"
       if self.z != None:
           info = info + "[Z]"
       if self.time != None:
           info = info + "[T]"
       return info
       
    def __str__(self):
        return self._info
    
    def __unicode__(self):
        return self._info
        
    _info = property(_getinfo)
    x = self.xy._xarray
    y = self.xy._yarray
    
class SubCoordinates:
    def __init__(self, **kwargs):
        self.x = None
        self.y = None
        self.z = None
        self.time = None
        if "x" in kwargs:
            self.x = kwargs["x"]
        if "y" in kwargs:
            self.y = kwargs["y"]
        if "z" in kwargs:
            self.z = kwargs["Z"]
        if "time" in kwargs:
            self.time = kwargs["time"]
       
       
         
            
            
