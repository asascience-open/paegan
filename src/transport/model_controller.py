import unittest
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
from src.transport.shoreline import Shoreline

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
            * models (list object) no default, so far there is a transport model and a behavior model
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
        self._models = kwargs.pop('models', None)
        self._dirty = True
        self._particles = []

        # Create shoreline
        if self.use_shoreline == True:
            self._shoreline = Shoreline()

        # Inerchangeables
        if "point" in kwargs:
            self._point = kwargs.pop('point')
        elif "latitude" and "longitude" in kwargs:
            self._latitude = kwargs.pop('latitude')
            self._longitude = kwargs.pop('longitude') 
        else:
            raise TypeError("must provide a point geometry object or latitude and longitude")

        # Errors
        if "nstep" in kwargs:
            self._nstep = kwargs.pop('nstep')
        else:
            raise TypeError("must provide the number of timesteps")

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

    def set_models(self, mod):
        self._models = mod
    def get_models(self):
        return self._models
    models = property(get_models, set_models)

    def set_particles(self, parts):
        self._particles = parts
    def get_particles(self):
        return self._particles
    particles = property(get_particles, set_particles)

    def __str__(self):
        return  " *** ModelController *** " + \
                "\nlatitude: " + str(self.latitude) + \
                "\nlongitude: " + str(self.longitude) + \
                "\ndepth: " + str(self.depth) + \
                "\nstart: " + str(self.start) +\
                "\nstep: " + str(self.step) +\
                "\nnstep: " + str(self.nstep) +\
                "\nnpart: " + str(self.npart) +\
                "\nmodels: " + str(self.models) +\
                "\nuse_bathymetry: " + str(self.use_bathymetry) +\
                "\nuse_shoreline: " + str(self.use_shoreline)

    def check_bounds(self, **kwargs):
        # shoreline
        starting = kwargs.pop('starting')
        ending = kwargs.pop('ending')

        if self.use_shoreline == True:
            self._shoreline.intersect(starting, ending)

        # bathymetry
        #if self.use_bathymetry == True:
            # get bathymetry

    def generate_map(self):
        # Plot here

    # The transport part
    def run(self):
        # data from model controller inputs
        times = range(0,(self.step*self.nstep)+1,self.step)
        u_get=[]
        v_get=[]
        z_get=[]
        start_lat = self.latitude
        start_lon = self.longitude
        start_depth = self.depth
        start_time = self.start
        models = self.modelsjects

        for x in xrange(0, self.npart): # loop over number of particles chosen

            p = Particle() # create a particle instance (from particle.py)
            if start_time == None:
                raise TypeError("must provide a stat time to run the models")
            loc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=start_time) # make location4d instance
            p.location = loc # set particle location

            # loop over number of time steps
            for i in xrange(0, len(times)-1): 

                try:
                    modelTimestep = times[i+1] - times[i]
                    calculatedTime = times[i+1]
                except:
                    modelTimestep = times[i] - times[i-1]
                    calculatedTime = times[i] + modelTimestep
                    
                current_location = p.location

                if Transport in models:
                    transport_model = Transport(horizDisp=0.05, vertDisp=0.00003) # create a transport instance
                    movement = transport_model.move(current_location.latitude, current_location.longitude, current_location.depth, u_get, v_get, z_get, modelTimestep)
                    newloc = Location4D(latitude=movement['lat'], longitude=movement['lon'], depth=movement['depth'])
                    newloc.u = movement['u']
                    newloc.v = movement['v']
                    newloc.z = movement['z']
                    newloc.time = start_time + timedelta(seconds=calculatedTime)

                    newloc = check_bounds(p.get_current_location, newloc);

                    p.location = newloc

                #if 'behaviour' in models:
                #behavior_movement = 


            self._particles.append(p)
