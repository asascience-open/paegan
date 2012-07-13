import unittest
import time
import numpy as np
import netCDF4
from datetime import datetime, timedelta
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from paegan.transport.shoreline import Shoreline
from paegan.transport.bathymetry import Bathymetry
from multiprocessing import Value
import multiprocessing

    
class Consumer(multiprocessing.Process):
    
    def __init__(self, task_queue, result_queue, n_run):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.n_run = n_run
        
    def run(self):
        proc_name = self.name
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                #print '%s: Exiting' % proc_name
                self.task_queue.task_done()
                #print dir(self.n_run)
                self.n_run.value = self.n_run.value - 1
                break
            #print '%s: %s' % (proc_name, next_task)
            answer = next_task()
            self.task_queue.task_done()
            self.result_queue.put(answer)
        return

class DataController(object):
    def __init__(self, url, n_run, get_data, updating,
                 uname, vname, kname, init_size):
        self.url = url
        #self.local = Dataset(".cache/localcache.nc", 'w')
        self.n_run = n_run
        self.get_data = get_data
        self.updating = updating
        self.uname = uname
        self.vname = vname
        self.kname = kname
        self.inds = np.arange(init_size)
        self.init_size = init_size
    def __call__(self):
        c = 0
        self.remote = netCDF4.Dataset(self.url)
        while self.n_run.value > 1:
            #print self.n_run.value
            if self.get_data.value == True:
                if c == 0:
                    self.updating.value = True
                    self.local = netCDF4.Dataset("localcache.nc", 'w')
                    
                    # Create dimensions for u and v variables
                    self.local.createDimension('time', None)
                    self.local.createDimension('level', None)
                    self.local.createDimension('x', None)
                    self.local.createDimension('y', None)
                    
                    # Create 3d or 4d u and v variables
                    if self.remote.variables[self.uname].ndim == 4:
                        self.ndim = 4
                        dimensions = ('time', 'level', 'y', 'x')
                    elif self.remote.variables[self.uname].ndim == 3:
                        self.ndim = 3
                        dimensions = ('time', 'y', 'x')
                        
                    u = self.local.createVariable(self.uname, 
                        'f8', dimensions, zlib=False,
                        fill_value=self.remote.variables[self.uname].missing_value)
                    v = self.local.createVariable(self.vname, 
                        'f8', dimensions, zlib=False,
                        fill_value=self.remote.variables[self.vname].missing_value)
                    if self.kname != None:
                        k = self.local.createVariable(self.kname, 
                            'f8', dimensions, zlib=False,
                            fill_value=self.remote.variables[self.kname].missing_value)
                            
                    u[:] = self.remote.variables[self.uname][self.inds, :10,:10, :10] #:]
                    v[:] = self.remote.variables[self.vname][self.inds, :10,:10, :10] #:]
                    if self.kname != None:
                        k[:] = self.remote.variables[self.kname][self.inds, :]
                    self.local.sync()
                    self.local.close()
                    c += 1
                    self.inds = self.inds + self.init_size
                    self.updating.value = False
                    self.get_data.value = False
                else:
                    self.updating.value = True
                    self.local = netCDF4.Dataset("localcache.nc", 'a')                    
                    self.local.variables[self.uname][self.inds,:] = \
                        self.remote.variables[self.uname][self.inds,:]
                    self.local.variables[self.vname][self.inds,:] = \
                        self.remote.variables[self.vname][self.inds,:]
                    if self.kname != None:
                        self.local.variables[self.kname][self.inds,:] = \
                            self.remote.variables[self.kname][self.inds,:]
                    self.local.sync()
                    self.local.close()
                    c += 1
                    self.updating.value = False
                    self.get_data.value = False
            else:
                pass
        return
            
        
class ForceParticle(object):
    from paegan.transport.shoreline import Shoreline
    from paegan.transport.bathymetry import Bathymetry
    #from paegan.cdm.dataset import CommonDataset
    def __str__(self):
        return self.part.__str__()

    def __init__(self, part, times, start_time, models, 
                 u, v, z, point, usebathy, useshore, usesurface,
                 get_data, n_run, updating):
        self.point = point
        self.part = part
        self.times = times
        self.start_time = start_time
        self.models = models
        self.u = u
        self.v = v
        self.z = z
        self.usebathy = usebathy
        self.useshore = useshore
        self.usesurface = usesurface
        self.get_data = get_data
        self.n_run = n_run
        self.updating = updating
        
    def __call__(self):
        if self.usebathy == True:
            self._bathymetry = Bathymetry(point=self.point)
        else:
            self._bathymetry = None
        if self.useshore == True:
            self._shoreline = Shoreline(point=self.point)
        else:
            self._shoreline = None

        part = self.part
        times = self.times
        start_time = self.start_time
        models = self.models
        
        # Get data from local netcdf here
        # dataset = CommonDataset(".cache/localcache.nc")
        # if need a time that is outside of what we have:
        #     self.get_data = True
        while self.get_data == True and self.updating == True:
            pass
        u = self.u # dataset.get_values(self.uname, )
        v = self.v # dataset.get_values(self.vname, )
        z = self.z # dataset.get_values(self.kname, )

        # loop over timesteps
        for i in xrange(0, len(times)-1): 
            try:
                modelTimestep = times[i+1] - times[i]
                calculatedTime = times[i+1]
            except:
                modelTimestep = times[i] - times[i-1]
                calculatedTime = times[i] + modelTimestep
               
            newtime = start_time + timedelta(seconds=calculatedTime)
            newloc = None
            
            # loop over models - sort these in the order you want them to run
            for model in models:
                movement = model.move(part.location, u[i], v[i], z[i], modelTimestep)
                newloc = Location4D(latitude=movement['latitude'], longitude=movement['longitude'], depth=movement['depth'], time=newtime)
                if newloc: # changed p.location to part.location
                    self.boundary_interaction(self._bathymetry, self._shoreline, self.usebathy,self.useshore,self.usesurface,
                        particle=part, starting=part.location, ending=newloc,
                        distance=movement['distance'], angle=movement['angle'], 
                        azimuth=movement['azimuth'], reverse_azimuth=movement['reverse_azimuth'], 
                        vertical_distance=movement['vertical_distance'], vertical_angle=movement['vertical_angle'])
        return part
    
    def boundary_interaction(self, bathy, shore, usebathy, useshore, usesurface,
                             **kwargs):
        """
            Returns a list of Location4D objects
        """
        
        particle = kwargs.pop('particle')
        starting = kwargs.pop('starting')
        ending = kwargs.pop('ending')

        # bathymetry
        if usebathy:
            pt = bathy.intersect(start_point=starting.point,
                                 end_point=ending.point,
                                 distance=kwargs.get('vertical_distance'),
                                 angle=kwargs.get('vertical_angle'))
            if pt:
                ending.latitude = pt.latitude
                ending.longitude = pt.longitude
                ending.depth = pt.depth

        # shoreline
        if useshore:
            intersection_point = shore.intersect(start_point=starting.point, end_point=ending.point)
            if intersection_point:
                # Set the intersection point
                hitpoint = Location4D(point=intersection_point['point'])
                particle.location = hitpoint
                resulting_point = shore.react(start_point=starting,
                                              end_point=ending,
                                              hit_point=hitpoint,
                                              feature=intersection_point['feature'],
                                              distance=kwargs.get('distance'),
                                              angle=kwargs.get('angle'),
                                              azimuth=kwargs.get('azimuth'),
                                              reverse_azimuth=kwargs.get('reverse_azimuth'))
                ending.latitude = resulting_point.latitude
                ending.longitude = resulting_point.longitude
                ending.depth = resulting_point.depth

        # sea-surface
        if usesurface:
            if ending.depth > 0:
                ending.depth = 0

        particle.location = ending
    
