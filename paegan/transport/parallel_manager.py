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
from paegan.cdm.dataset import CommonDataset
import os
import random
    
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

                self.n_run.value = self.n_run.value - 1
                break
            #print '%s: %s' % (proc_name, next_task)
            answer = next_task()
            self.task_queue.task_done()
            self.result_queue.put(answer)
        return

class DataController(object):
    def __init__(self, url, n_run, get_data, updating,
                 uname, vname, wname, init_size, particle_get,
                 xname, yname, tname, zname):
        self.url = url
        #self.local = Dataset(".cache/localcache.nc", 'w')
        self.n_run = n_run
        self.get_data = get_data
        self.updating = updating
        self.uname = uname
        self.vname = vname
        self.wname = wname
        self.xname = xname
        self.yname = yname
        self.zname = zname
        self.tname = tname
        self.inds = np.arange(init_size)
        self.init_size = init_size
        self.particle_get = particle_get
    def __call__(self):
        c = 0
        self.remote = netCDF4.Dataset(self.url)
        cachepath = os.path.join(os.path.dirname(__file__),"_cache","localcache.nc")
        while self.n_run.value > 1:
            #print self.n_run.value
            if self.get_data.value == True:
                if c == 0:
                    self.updating.value = True
                    while self.particle_get == True:
                        pass
                    self.local = netCDF4.Dataset(cachepath, 'w')
                    
                    # Create dimensions for u and v variables
                    self.local.createDimension('time', None)
                    self.local.createDimension('level', None)
                    self.local.createDimension('x', None)
                    self.local.createDimension('y', None)
                    
                    # Create 3d or 4d u and v variables
                    if self.remote.variables[self.uname].ndim == 4:
                        self.ndim = 4
                        dimensions = ('time', 'level', 'y', 'x')
                        coordinates = "time z lon lat"
                    elif self.remote.variables[self.uname].ndim == 3:
                        self.ndim = 3
                        dimensions = ('time', 'y', 'x')
                        coordinates = "time lon lat"
                    try:
                        fill = self.remote.variables[self.uname].missing_value
                    except:
                        fill = np.nan
                        
                    u = self.local.createVariable('u', 
                        'f8', dimensions, zlib=False,
                        fill_value=fill)
                    v = self.local.createVariable('v', 
                        'f8', dimensions, zlib=False,
                        fill_value=fill)
                    if self.wname != None:
                        w = self.local.createVariable('w', 
                            'f8', dimensions, zlib=False,
                            fill_value=fill)
                    '''    
                    except:
                       
                        u = self.local.createVariable('u', 
                            'f8', dimensions, zlib=False,
                            )
                        v = self.local.createVariable('v', 
                            'f8', dimensions, zlib=False,
                            )
                        if self.wname != None:
                            w = self.local.createVariable('w', 
                                'f8', dimensions, zlib=False,
                                )
                    '''
                    if self.remote.variables[self.xname].ndim == 2:
                        lon = self.local.createVariable('lon',
                                'f8', ("y", "x"), zlib=False,
                                )
                        lat = self.local.createVariable('lat',
                                'f8', ("y", "x"), zlib=False,
                                )
                        lon[:] = self.remote.variables[self.xname][50:60, 50:60]
                        lat[:] = self.remote.variables[self.yname][50:60, 50:60]
                    if self.remote.variables[self.xname].ndim == 1:
                        lon = self.local.createVariable('lon',
                                'f8', ("x"), zlib=False,
                                )
                        lat = self.local.createVariable('lat',
                                'f8', ("y"), zlib=False,
                                )
                        lon[:] = self.remote.variables[self.xname][50:60]
                        lat[:] = self.remote.variables[self.yname][50:60]
                    
                    if self.zname != None:            
                        if self.remote.variables[self.zname].ndim == 4:
                            z = self.local.createVariable('z',
                                'f8', ("time","level","y","x"), zlib=False,
                                )  
                            z[:] = self.remote.variables[self.zname][self.inds, :, :, :]
                        elif self.remote.variables[self.zname].ndim == 3:
                            z = self.local.createVariable('z',
                                'f8', ("level","y","x"), zlib=False,
                                )
                            z[:] = self.remote.variables[self.zname][:, :, :]
                        #elif self.remote.variables[zname].ndim == 2:
                        #    z = self.local.createVariable('lon',
                        #        'f8', ("",), zlib=False,
                        #        )
                        elif self.remote.variables[self.zname].ndim ==1:
                            z = self.local.createVariable('z',
                                'f8', ("level",), zlib=False,
                                )
                            z[:] = self.remote.variables[self.zname][1:3]
                    
                    time = self.local.createVariable('time',
                                'f8', ("time",), zlib=False,
                                )
                    if self.tname != None:
                        time[:] = self.remote.variables[self.tname][self.inds]  
                    
                    u[:] = self.remote.variables[self.uname][self.inds, 1:3, 50:60, 50:60] #:]
                    v[:] = self.remote.variables[self.vname][self.inds, 1:3, 50:60, 50:60] #:]
                    u.coordinates = coordinates
                    v.coordinates = coordinates
                    if self.wname != None:
                        w[:] = self.remote.variables[self.wname][self.inds, :]
                        w.coordinates = coordinates
                    self.local.sync()
                    self.local.close()
                    c += 1
                    self.inds = self.inds + self.init_size
                    self.updating.value = False
                    self.get_data.value = False
                else:
                    
                    self.updating.value = True
                    self.local = netCDF4.Dataset(cachepath, 'a')                  
                    self.local.variables["u"][self.inds, 0:2, :10, :10] = \
                        self.remote.variables[self.uname][self.inds, 1:3, 50:60, 50:60]
                    self.local.variables["v"][self.inds, 0:2, :10, :10] = \
                        self.remote.variables[self.vname][self.inds, 1:3, 50:60, 50:60]
                    if self.tname != None:
                        self.local.variables["time"][self.inds] = \
                            self.remote.variables[self.tname][self.inds]
                    if self.wname != None:
                        self.local.variables["w"][self.inds,:] = \
                            self.remote.variables[self.wname][self.inds,:]
                    self.local.sync()
                    self.local.close()
                    c += 1
                    self.inds = self.inds + self.init_size
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
                 point, usebathy, useshore, usesurface,
                 get_data, n_run, updating, particle_get):
        self.url =  os.path.join(os.path.dirname(__file__),"_cache","localcache.nc")
        #self.uname = uname
        #self.vname = vname
        #self.wname = wname
        self.point = point
        self.part = part
        self.times = times
        self.start_time = start_time
        self.models = models
        #self.u = u
        #self.v = v
        #self.z = z
        self.usebathy = usebathy
        self.useshore = useshore
        self.usesurface = usesurface
        self.get_data = get_data
        self.n_run = n_run
        self.updating = updating
        self.particle_get = particle_get
        
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
        while self.get_data.value == True:
            pass
        self.dataset = CommonDataset(self.url, dataset_type="rgrid")
        self.dataset.closenc()
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
            
            
            # Get data from local netcdf here
            # dataset = CommonDataset(".cache/localcache.nc")
            
            # if need a time that is outside of what we have:e
            while self.get_data.value == True:
                pass
            self.particle_get.value = True
            self.dataset.opennc()

            try:
                #print i
                #print self.dataset.nc.variables['u'].shape
                u = self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location )
                v = self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location )
                #u = np.mean(np.mean(np.ma.masked_array(u, np.isnan(u))))
                #v = np.mean(np.mean(np.ma.masked_array(v, np.isnan(v))))
                w = 0#self.z # dataset.get_values('w', )
                self.dataset.closenc()
            except IndexError:
                self.dataset.closenc()
                self.particle_get.value = False
                if self.get_data.value != True:
                    self.get_data.value = True
                while self.get_data.value == True:
                    pass
                self.particle_get.value = True
                self.dataset.opennc()
                u = self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location )
                v = self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location )
                #u = np.mean(np.mean(np.ma.masked_array(u, np.isnan(u))))
                #v = np.mean(np.mean(np.ma.masked_array(v, np.isnan(v))))
                w = 0#self.z # dataset.get_values('w', )
                self.dataset.closenc()
            # loop over models - sort these in the order you want them to run
            for model in models:
                movement = model.move(part.location, u, v, w, modelTimestep)
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
    
