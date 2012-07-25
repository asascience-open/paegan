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
        self.n_run.value = self.n_run.value + 1
    def run(self):
        proc_name = self.name
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                #print '%s: Exiting' % proc_name
                self.n_run.value = self.n_run.value - 1
                self.task_queue.task_done()

                
                break
            #print '%s: %s' % (proc_name, next_task)
            answer = next_task()
            self.task_queue.task_done()
            self.result_queue.put(answer)
        return

class DataController(object):
    def __init__(self, url, n_run, get_data, updating,
                 init_size, horiz_chunk, particle_get, times,
                 start_time, point_get, start,
                 **kwargs
                 ):
        self.url = url
        #self.local = Dataset(".cache/localcache.nc", 'w')
        self.n_run = n_run
        self.get_data = get_data
        self.updating = updating
        self.inds = None#np.arange(init_size+1)
        self.time_size = init_size
        self.horiz_size = horiz_chunk
        self.particle_get = particle_get
        self.point_get = point_get
        self.low_memory = kwargs.get("low_memory", False)
        self.start_time = start_time
        self.times = times
        
        self.start = start

    
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
        #print "updating local data"
        if self.horiz_size == 'all':
            y, y_1 = 0, shape[-2]
            x, x_1 = 0, shape[-1]
        else:
            r = self.horiz_size
            x, x_1 = self.point_get.value[2]-r, self.point_get.value[2]+r+1
            y, y_1 = self.point_get.value[1]-r, self.point_get.value[1]+r+1
            if y < 0:
                y = 0
            if x < 0:
                x = 0
            if y_1 > shape[-2]:
                y_1 = shape[-2]
            if x_1 > shape[-1]:
                x_1 = shape[-1]
        for local, remote in zip(localvars, remotevars):
            for i, time in enumerate(inds[:]):
                if time+1 > shape[0] - 1:
                    time_1 = shape[0]
                else:
                    time_1 = time+1
                #print time, time_1
                if self.low_memory:
                 
                    for z in range(shape[1]):
                        if z + 1 > shape[1] - 1:
                            z_1 = shape[1]
                        else:
                            z_1 = z + 1
                    #for y in range(0,shape[2],8):
                    #    if y + 8 > shape[2] - 1:
                    #        y_1 = shape[2]
                    #    else:
                    #        y_1 = y + 8
                        if len(shape) == 4:
                            #    for x in range(shape[3]):
                            #        if x + 1 > shape[3] - 1:
                            #            x_1 = shape[3]
                            #        else:
                            #            x_1 = x + 1
                            local[time:time_1, z:z_1, y:y_1, x:x_1] = remote[time:time_1,  z:z_1, y:y_1, x:x_1]
                        else:
                            if z == 0:
                                local[time:time_1, y:y_1, x:x_1] = remote[time:time_1, y:y_1, x:x_1]
                
                else:
                    if len(shape) == 4:
                        local[time:time_1, :, y:y_1, x:x_1] = remote[time:time_1,  :, y:y_1, x:x_1]
                    else:
                        local[time:time_1, y:y_1, x:x_1] = remote[time:time_1, y:y_1, x:x_1]

    def __call__(self):
        c = 0
        self.dataset = CommonDataset(self.url)
        
        self.get_variablenames_for_model()
        self.remote = self.dataset.nc
        cachepath = os.path.join("/home/acrosby/local.nc")#os.path.dirname(__file__),"_cache","localcache.nc")
        times = self.times
        start_time = self.start_time
        
        modelTimestep = []
        calculatedTime = []
        newtimes = []
        for i in xrange(0, len(times)-1):
            try:
                modelTimestep.append(times[i+1] - times[i])
                calculatedTime.append(times[i+1])
            except:
                modelTimestep.append(times[i] - times[i-1])
                calculatedTime.append(times[i] + modelTimestep[i])
               
            newtimes.append(start_time + timedelta(seconds=calculatedTime[i]))
      
        timevar = self.dataset.gettimevar(self.uname)
        time_indexs = timevar.nearest_index(newtimes)
        
        self.inds = np.unique(time_indexs)
                
        while self.n_run.value > 1:
            #print self.n_run.value
            if self.get_data.value == True:
                if c == 0:
                    indices = self.dataset.get_indices(self.uname, timeinds=[np.asarray([0])], point=self.start)
                    self.point_get.value = [self.inds[0], indices[-2], indices[-1]]
                
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
                            'f', dimensions, zlib=False,
                            )
                        v = self.local.createVariable('v', 
                            'f', dimensions, zlib=False,
                            )
                        v.coordinates = coordinates
                        u.coordinates = coordinates
                        
                        if self.wname != None:
                            w = self.local.createVariable('w', 
                                'f', dimensions, zlib=False,
                                )
                            w.coordinates = coordinates
                        if self.temp_name != None and self.salt_name != None:        
                            temp = self.local.createVariable('temp', 
                                'f', dimensions, zlib=False,
                                )
                            salt = self.local.createVariable('salt', 
                                'f', dimensions, zlib=False,
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
                    
                    #try:
                    #    current_inds = self.inds[0:(c+1) * self.init_size]
                    #except:
                    #    current_inds = self.inds[0:]
                    if self.point_get.value[0]+self.time_size > np.max(self.inds):
                        current_inds = np.arange(self.point_get.value[0], np.max(self.inds)+1)
                    else:
                        current_inds = np.arange(self.point_get.value[0],self.point_get.value[0] + self.time_size)
                           
                    self.get_remote_data(localvars, remotevars, current_inds, shape) 
                    
                    self.local.sync()
                    self.local.close()
                    c += 1
                    #self.inds = self.inds + self.init_size
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
                    
                    #try:
                    #    current_inds = self.inds[c*self.init_size:(c+1) * self.init_size]
                    #except:
                    #    current_inds = self.inds[c*self.init_size:]
                    if self.point_get.value[0]+self.time_size > np.max(self.inds):
                        current_inds = np.arange(self.point_get.value[0], np.max(self.inds)+1)
                    else:
                        current_inds = np.arange(self.point_get.value[0],self.point_get.value[0] + self.time_size)
                           
                    self.get_remote_data(localvars, remotevars, current_inds, shape)
                    
                    self.local.sync()
                    self.local.close()
                    c += 1
                    #self.inds = self.inds + self.init_size
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

    def __init__(self, part, remotehydro, times, start_time, models, 
                 point, usebathy, useshore, usesurface,
                 get_data, n_run, updating, particle_get,
                 point_get):
        self.remotehydropath = remotehydro
        self.localpath =  os.path.join("/home/acrosby/local.nc")#os.path.dirname(__file__),"_cache","localcache.nc")
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
        self.point_get = point_get
        
    def get_variablenames_for_model(self, dataset):
        getname = dataset.get_varname_from_stdname
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

        coords = dataset.get_coord_names(self.uname) 
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
        
    def check_cache_for_data(self, i):
        #need = True
        #while need:
        shape = self.dataset.nc.variables[self.uname].shape
        if shape[0] < i:
            time_need = True
        else:
            time_need = False
        if np.mean(np.mean(self.dataset.get_values('domain', timeinds=[np.asarray([i])], point=self.part.location ))) == 0:
            horiz_need = True
        else:
            horiz_need = False
        return horiz_need or time_need # return true if need data or false if dont
            
        
    def ask_for_new_data(self):
        pass
        
    def make_sure_data_in_cache(self, i):
        if self.get_data.value:
            self.dataset.closenc()
        while self.get_data.value == True:
            pass
        if self.dataset.nc == None:
            self.dataset.opennc()
        if self.check_cache_for_data(i):
            indices = self.dataset.get_indices('u', timeinds=[np.asarray([i-1])], point=self.part.location )
            self.point_get = [indices[0],indices[-2],indices[-1]]
            self.get_data.value = True  # Checkout data controller for update
            # Checkin data controller for update
            
      
    def get_data(self, i):
        if self.get_data.value:
            self.dataset.closenc()
        while self.get_data.value == True:
            pass
        self.particle_get.value = True
        if self.dataset.nc == None:
            self.dataset.opennc()
        u = np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location )))
        v = np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location )))
        if 'w' in self.dataset.nc.variables:
            w = np.mean(np.mean(self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location )))
        else:
            w = 0
        self.particle_get.value = False
        
        return u,v,w
        
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
        self.dataset = CommonDataset(self.localpath)
        self.dataset.closenc()
        
        modelTimestep = []
        calculatedTime = []
        newtimes = []
        for i in xrange(0, len(times)-1):
            try:
                modelTimestep.append(times[i+1] - times[i])
                calculatedTime.append(times[i+1])
            except:
                modelTimestep.append(times[i] - times[i-1])
                calculatedTime.append(times[i] + modelTimestep[i])
               
            newtimes.append(start_time + timedelta(seconds=calculatedTime[i]))
        
        
        remote = CommonDataset(self.remotehydropath)
        self.get_variablenames_for_model(remote)
        #remote_coord_names = remote.get_coord_names('u')
        #remote_nctime = remote.nc.variables[remote_coord_names['tname']]
        #time_indexs = netCDF4.date2index(newtimes, remote_nctime,
        #                                 select='nearest')
        timevar = remote.gettimevar(self.uname)
        time_indexs = timevar.nearest_index(newtimes)
        array_indexs = time_indexs - time_indexs[0]
        
        # loop over timesteps   
        for i, loop_i in zip(time_indexs, array_indexs):
            
            newloc = None
            
            
            # Get data from local netcdf here
            # dataset = CommonDataset(".cache/localcache.nc")
            
            # if need a time that is outside of what we have:e
            while self.get_data.value == True:
                pass
            self.particle_get.value = True
            self.dataset.opennc()
            
            self.make_sure_data_in_cache(i)
            u, v, w = self.get_data(i)
            '''
            try:
                if np.mean(np.mean(self.dataset.get_values('domain', timeinds=[np.asarray([i])], point=self.part.location ))) == 0:
                    indices = self.dataset.get_indices('u', timeinds=[np.asarray([i])], point=self.part.location )
                    self.point_get.value = [i, indices[-2], indices[-1]]
                    self.dataset.closenc()
                    self.particle_get.value = False
                    if self.get_data.value != True:
                        self.get_data.value = True
                    while self.get_data.value == True:
                        pass
                    self.particle_get.value = True
                    self.dataset.opennc()
                u = np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location )))
                v = np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location )))
                if 'w' in self.dataset.nc.variables:
                    w = np.mean(np.mean(self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location )))
                else:
                    w = 0
                self.dataset.closenc()
                
            except:
                self.dataset.closenc()
                self.particle_get.value = False
                if self.get_data.value != True:
                    self.get_data.value = True
                while self.get_data.value == True:
                    pass
                self.particle_get.value = True
                self.dataset.opennc()
                if np.mean(np.mean(self.dataset.get_values('domain', timeinds=[np.asarray([i])], point=self.part.location ))) == 0:
                    indices = self.dataset.get_indices('u', timeinds=[np.asarray([i])], point=self.part.location )
                    self.point_get.value = [i, indices[-2], indices[-1]]
                    self.dataset.closenc()
                    self.particle_get.value = False
                    if self.get_data.value != True:
                        self.get_data.value = True
                    while self.get_data.value == True:
                        pass
                    self.particle_get.value = True
                    self.dataset.opennc()
                u = np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location )))
                v = np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location )))
                if 'w' in self.dataset.nc.variables:
                    w = np.mean(np.mean(self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location )))
                else:
                    w = 0
                self.dataset.closenc()
            '''
            
            #print u, v
            if np.isnan(u) or np.isnan(v):
                self.dataset.opennc()
                u = np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location, num=2 )))
                v = np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location, num=2 )))
                if 'w' in self.dataset.nc.variables:
                    w = np.mean(np.mean(self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location )))
                else:
                    w = 0
                self.dataset.closenc()
            
            # loop over models - sort these in the order you want them to run
            for model in models:
                movement = model.move(part.location, u, v, w, modelTimestep[loop_i])
                newloc = Location4D(latitude=movement['latitude'], longitude=movement['longitude'], depth=movement['depth'], time=newtimes[loop_i])
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
                
        # bathymetry
        if usebathy:
            bintersect = bathy.intersect(start_point=starting,
                                         end_point=ending,
                                        )
            if bintersect:
                pt = bathy.react(type='hover', end_point=ending)
                ending.latitude = pt.latitude
                ending.longitude = pt.longitude
                ending.depth = pt.depth

        # sea-surface
        if usesurface:
            if ending.depth > 0:
                ending.depth = 0

        particle.location = ending
    
