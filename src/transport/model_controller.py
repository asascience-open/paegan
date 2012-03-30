#import unittest
import random
import matplotlib
import matplotlib.pyplot
#from mpl_toolkits.mplot3d import Axes3D
import numpy
from datetime import datetime, timedelta
from src.transport.models.transport import Transport
from src.transport.particles.particle import Particle
from src.transport.location4d import Location4D
from src.utils.asarandom import AsaRandom

class ModelController(object):
    """
        Controls the models
    """
    def __init__(self, **kwargs):

    	""" 
    		Mandatory named arguments:
            * point (Shapely Point Object) no default
            * depth (meters) default 0
            * start (DateTime Object) none
            * step (seconds) default 3600
            * npart (number of particles) default 1
            * nstep (number of steps) no default
            point is interchangeable with:
            * latitude (DD) no default
            * longitude (DD) no default
            * depth (meters) default 0
        """

        # Defaults
        self._use_shoreline = kwargs.pop('use_shoreline', True)
        self._use_bathymetry = kwargs.pop('use_bathymetry', True)
        self._depth = kwargs.pop('depth', 0)
        self._npart = kwargs.pop('npart', 1)
        self._start = kwargs.pop('start', None)
        self._step = kwargs.pop('step', 3600)
        self._dirty = True

        # Inerchangeables
        if "point" in kwargs:
            self._point = kwargs.pop('point')
        elif "latitude" and "longitude" in kwargs:
            self._latitude = kwargs.pop('latitude')
            self._longitude = kwargs.pop('longitude') 
        else:
            raise TypeError( "must provide a point geometry object or latitude and longitude" )

        # Errors
        if "nstep" in kwargs:
            self._nstep = kwargs.pop('nstep')
        else:
            raise TypeError( "must provide the number of timesteps" )

    def set_point(self, point):
        self._point = point
        self._dirty = False
    def get_point(self):
        if self._dirty:
            self._point = Point(self._longitude, self._latitude, self._depth)
        return self._point
    point = property(get_point, set_point)

    def set_latitude(self, lat):
        self._latitude = lat
        self._dirty = True
    def get_latitude(self):
        return self._latitude
    latitude = property(get_latitude, set_latitude)

    def set_longitude(self, lon):
        self._longitude = lon
        self._dirty = True
    def get_longitude(self):
        return self._longitude
    longitude = property(get_longitude, set_longitude)

    def set_depth(self, dep):
        self._depth = dep
        self._dirty = True
    def get_depth(self):
        return self._depth
    depth = property(get_depth, set_depth)

    def set_start(self, sta):
        self._start = sta
    def get_start(self):
        return self._start
    start = property(get_start, set_start)

    def set_step(self, ste):
        self._step = ste
    def get_step(self):
        return self._step
    step = property(get_step, set_step)

    def set_nstep(self, nst):
        self._nstep = nst
    def get_nstep(self):
        return self._nstep
    nstep = property(get_nstep, set_nstep)

    def set_use_shoreline(self, sho):
        self._use_shoreline = sho
    def get_use_shoreline(self):
        return self._use_shoreline
    use_shoreline = property(get_use_shoreline, set_use_shoreline)

    def set_use_bathymetry(self, bat):
        self._use_bathymetry = bat
    def get_use_bathymetry(self):
        return self._use_bathymetry
    use_bathymetry = property(get_use_bathymetry, set_use_bathymetry)

    def set_npart(self, npa):
        self._npart = npa
    def get_npart(self):
        return self._npart
    npart = property(get_npart, set_npart)

    def __str__(self):
        return  " *** ModelController *** " + \
                "\nlatitude: " + str(self.latitude) + \
                "\nlongitude: " + str(self.longitude) + \
                "\ndepth: " + str(self.depth) + \
                "\nstart: " + str(self.start) +\
                "\nstep: " + str(self.step) +\
                "\nnstep: " + str(self.nstep) +\
                "\nnpart: " + str(self.npart) +\
                "\nuse_bathymetry: " + str(self.use_bathymetry) +\
                "\nuse_shoreline: " + str(self.use_shoreline)

    def test_multiple_particles(self):
        # Constants

        horizDisp=0.05 
        vertDisp=0.00003 
        times = range(0,(self.step*self.nstep)+1,self.step)
        start_lat = self.latitude
        start_lon = self.longitude
        start_depth = self.depth
        start_time = self.time

        # empty array for storing resulting particle objects
        arr = []

        # Get u, v, and z from start location and depth
        u=[]
        v=[]
        z=[]

        for x in xrange(0, self.npart):
            p = Particle() # create a particle instance

            loc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=start_time)
            p.location = loc # set particle location

            for i in xrange(0, len(times)-1):
                transport_model = Transport() # create a transport instance
                current_location = p.location
                try:
                    modelTimestep = times[i+1] - times[i]
                    calculatedTime = times[i+1]
                except:
                    modelTimestep = times[i] - times[i-1]
                    calculatedTime = times[i] + modelTimestep
                movement = transport_model.move(current_location.latitude, current_location.longitude, current_location.depth, u[i], v[i], z[i], horizDisp, vertDisp, modelTimestep)

                # behaviours
                #behaviour_movement = 
                
                # shoreline
                #if self.use_shoreline == True:

                # bathymetry
                #if self.use_bathymetry == True:
                
                newloc = Location4D(latitude=movement['lat'], longitude=movement['lon'], depth=movement['depth'])
                newloc.u = movement['u']
                newloc.v = movement['v']
                newloc.z = movement['z']
                newloc.time = start_time + timedelta(seconds=calculatedTime)
                p.location = newloc
            arr.append(p)
