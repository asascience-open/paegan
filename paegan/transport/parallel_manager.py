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
                 init_size, particle_get,
                 ):
        self.url = url
        #self.local = Dataset(".cache/localcache.nc", 'w')
        self.n_run = n_run
        self.get_data = get_data
        self.updating = updating
        #self.uname = None
        #self.vname = None
        #self.wname = None
        #self.xname = None
        #self.yname = None
        #self.zname = None
        #self.tname = None
        #self.temp_name = None
        #self.salt_name = None
        self.inds = np.arange(init_size)
        self.init_size = init_size
        self.particle_get = particle_get
    
    def get_variablenames_for_model(self):
        getname = self.dataset.get_varname_from_stdname
        self.uname = getname('eastward_sea_water_velocity') 
        self.vname = getname('northward_sea_water_velocity') 
        self.wname = getname('upward_sea_water_velocity')
        if len(self.uname) > 0:
            self.uname = self.uname[0]
        else:
            self.uname = None
        if len(self.vname) > 0:
            self.vname = self.vname[0]
        else:
            self.vname = None
        if len(self.wname) > 0:
            self.wname = self.wname[0]
        else:
            self.wname = None

        coords = self.dataset.get_coord_names(self.uname) 
        self.xname = coords['xname'] 
        self.yname = coords['yname']
        self.zname = coords['zname']
        self.tname = coords['tname']
        self.temp_name = getname('sea_water_temperature') 
        self.salt_name = getname('sea_water_salinity')
        
        if len(self.temp_name) > 0:
            self.temp_name = self.temp_name[0]
        else:
            self.temp_name = None       
        if len(self.salt_name) > 0:
            self.salt_name = self.salt_name[0]
        else:
            self.salt_name = None
        self.tname = None ## temporary
    
    def get_remote_data(self, localvars, remotevars, inds, shape):
        for local, remote in zip(localvars, remotevars):
            for time in inds[:]:
                if time + 1 > shape[0] - 1:
                    time_1 = shape[0]
                else:
                    time_1 = time + 1
                for z in range(shape[1]):
                    if z + 1 > shape[1] - 1:
                        z_1 = shape[1]
                    else:
                        z_1 = z + 1
                    for y in range(shape[2]):
                        if y + 1 > shape[2] - 1:
                            y_1 = shape[2]
                        else:
                            y_1 = y + 1

                        print time, time_1, z, z_1, y, y_1
                        if len(shape) == 4:
                            for x in range(shape[3]):
                                if x + 1 > shape[3] - 1:
                                    x_1 = shape[3]
                                else:
                                    x_1 = x + 1
                                local[time:time_1, z:z_1, y:y_1, x:x_1] = remote[time:time_1, z:z_1, y:y_1, x:x_1]
                        else:
                            local[time:time_1, z:z_1, y:y_1] = remote[time:time_1, z:z_1, y:y_1]
       
    def __call__(self):
        c = 0
        self.dataset = CommonDataset(self.url)
        
        self.get_variablenames_for_model()
        self.remote = self.dataset.nc
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
                    shape = self.remote.variables[self.uname].shape
                    try:
                        fill = self.remote.variables[self.uname].missing_value
                    except:
                        fill = None
                    
                    if fill == None:
                        u = self.local.createVariable('u', 
                            'f', dimensions, #zlib=False,
                            )
                        v = self.local.createVariable('v', 
                            'f', dimensions, #zlib=False,
                            )
                        v.coordinates = coordinates
                        u.coordinates = coordinates
                        
                        if self.wname != None:
                            w = self.local.createVariable('w', 
                                'f', dimensions, #zlib=False,
                                )
                            w.coordinates = coordinates
                        if self.temp_name != None and self.salt_name != None:        
                            temp = self.local.createVariable('temp', 
                                'f', dimensions, #zlib=False,
                                )
                            salt = self.local.createVariable('salt', 
                                'f', dimensions, #zlib=False,
                                )
                            temp.coordinates = coordinates
                            salt.coordinates = coordinates
                    else:    
                        u = self.local.createVariable('u', 
                            'f', dimensions, zlib=False,
                            fill_value=fill)
                        v = self.local.createVariable('v', 
                            'f', dimensions, zlib=False,
                            fill_value=fill)
                        v.coordinates = coordinates
                        u.coordinates = coordinates
                        
                        if self.wname != None:
                            w = self.local.createVariable('w', 
                                'f', dimensions, zlib=False,
                                fill_value=fill)
                            w.coordinates = coordinates
                        if self.temp_name != None and self.salt_name != None:        
                            temp = self.local.createVariable('temp', 
                                'f', dimensions, zlib=False,
                                fill_value=fill)
                            salt = self.local.createVariable('salt', 
                                'f', dimensions, zlib=False,
                                fill_value=fill)
                            temp.coordinates = coordinates
                            salt.coordinates = coordinates
                    
                    if self.remote.variables[self.xname].ndim == 2:
                        lon = self.local.createVariable('lon',
                                'f', ("y", "x"), zlib=False,
                                )
                        lat = self.local.createVariable('lat',
                                'f', ("y", "x"), zlib=False,
                                )
                    if self.remote.variables[self.xname].ndim == 1:
                        lon = self.local.createVariable('lon',
                                'f', ("x"), zlib=False,
                                )
                        lat = self.local.createVariable('lat',
                                'f', ("y"), zlib=False,
                                )
                    
                    if self.remote.variables[self.xname].ndim == 2:             
                        lon[:] = self.remote.variables[self.xname][:, :]
                        lat[:] = self.remote.variables[self.yname][:, :]
                    if self.remote.variables[self.xname].ndim == 1:
                        lon[:] = self.remote.variables[self.xname][:]
                        lat[:] = self.remote.variables[self.yname][:]
                    
                    localvars = [u, v,]
                    remotevars = [self.remote.variables[self.uname], 
                                  self.remote.variables[self.vname]]
                                  
                    if self.temp_name != None and self.salt_name != None:
                        localvars.append(temp)
                        localvars.append(salt)
                        remotevars.append(self.remote.variables[self.temp_name])
                        remotevars.append(self.remote.variables[self.salt_name])
                    if self.wname != None:
                        localvars.append(w)
                        remotevars.append(self.remote.variables[self.wname])
                        
                    if self.zname != None:            
                        if self.remote.variables[self.zname].ndim == 4:
                            z = self.local.createVariable('z',
                                'f', ("time","level","y","x"), zlib=False,
                                )  
                            remotez = self.remote.variables[self.zname]
                            localvars.append(z)
                            remotevars.append(remotez)
                        elif self.remote.variables[self.zname].ndim == 3:
                            z = self.local.createVariable('z',
                                'f', ("level","y","x"), zlib=False,
                                )
                            z[:] = self.remote.variables[self.zname][:, :, :]
                        elif self.remote.variables[self.zname].ndim ==1:
                            z = self.local.createVariable('z',
                                'f', ("level",), zlib=False,
                                )
                            z[:] = self.remote.variables[self.zname][:]
                    
                    time = self.local.createVariable('time',
                                'f8', ("time",), zlib=False,
                                )
                    if self.tname != None:
                        time[:] = self.remote.variables[self.tname][self.inds]

                    self.get_remote_data(localvars, remotevars, self.inds, shape) 
                    
                    self.local.sync()
                    self.local.close()
                    c += 1
                    self.inds = self.inds + self.init_size
                    self.updating.value = False
                    self.get_data.value = False

                else:
                    
                    self.updating.value = True
                    self.local = netCDF4.Dataset(cachepath, 'a')  
                    u = self.local.variables['u']
                    v = self.local.variables['v']
                    time = self.local.variables['time']
                    remoteu = self.remote.variables[self.uname]
                    remotev = self.remote.variables[self.vname]
                    remotetime = self.remote.variables[self.tname]
                    localvars = [u, v, ]
                    remotevars = [remoteu, remotev, ]
                    if self.salt_name != None and self.temp_name != None:
                        salt = self.local.variables['salt']
                        temp = self.local.variables['temp']
                        remotesalt = self.remote.variables[self.salt_name]
                        remotetemp = self.remote.variables[self.temp_name]
                        localvars.append(salt)
                        localvars.append(temp)
                        remotevars.append(remotesalt)
                        remotevars.append(remotetemp)
                    if self.wname != None:
                        w = self.local.variables['w']
                        remotew = self.remote.variables[self.wname]
                        localvars.append(w)
                        remotevars.append(remotew)
                    if self.zname != None:
                        remotez = self.remote.variables[self.zname]
                        if remotez.ndim == 4:
                            z = self.local.variables['z']
                            localvars.append(z)
                            remotevars.append(remotez)
                    if self.tname != None:
                        remotetime = self.remote.variables[self.tname]
                        time[self.inds] = self.remote.variables[self.inds]
                        
                    self.get_remote_data(localvars, remotevars, self.inds, shape)
                    
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
        self.point = point
        self.part = part
        self.times = times
        self.start_time = start_time
        self.models = models
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
            
            u = u[0]
            v = v[0]
            print u,v
            print self.part.location.longitude, self.part.location.latitude
            #if np.isnan(u) or np.isnan(v):
            #    u, v = random.uniform(-1, 1), random.uniform(-1, 1)

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
    
