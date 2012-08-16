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
#from paegan.logger import queue_logger

class Consumer(multiprocessing.Process):
    def __init__(self, task_queue, result_queue, n_run, lock):
        """
            This is the process class that does all the handling of queued tasks
        """
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.n_run = n_run
        self.lock = lock
        lock.acquire()
        self.n_run.value = self.n_run.value + 1
        lock.release()
        
    def run(self):
        proc_name = self.name
        while True:
            next_task = self.task_queue.get()
            #queue_logger.start()
            if next_task is None:
                # Poison pill means shutdown
                #print '%s: Exiting' % proc_name
                #queue_logger.logger().info("Particle " + proc_name + " at exit")
                #queue_logger.logger().info(str(self.n_run.value) + " remaining processes bfore")
                self.lock.acquire()
                self.n_run.value = self.n_run.value - 1
                #queue_logger.logger().info(str(self.n_run.value) + " remaining processes after")
                self.lock.release()
                self.task_queue.task_done()
                #queue_logger.stop()
                
                break
            #print '%s: %s' % (proc_name, next_task)
            answer = next_task(proc_name)
            self.task_queue.task_done()
            self.result_queue.put(answer)
        return

class DataController(object):
    def __init__(self, url, n_run, get_data, updating,
                 init_size, horiz_chunk, particle_get, times,
                 start_time, point_get, start,
                 **kwargs
                 ):
        """
            The data controller controls the updating of the
            local netcdf data cache
        """
        assert "cache" in kwargs
        self.cache_path = kwargs["cache"]
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
        """
            Method that does the updating of local netcdf cache
            with remote data
        """
        # If user specifies 'all' then entire xy domain is
        # grabbed, default is 4, specified in the model_controller
        if self.horiz_size == 'all':
            y, y_1 = 0, shape[-2]
            x, x_1 = 0, shape[-1]
        else:
            r = self.horiz_size
            x, x_1 = self.point_get.value[2]-r, self.point_get.value[2]+r+1
            y, y_1 = self.point_get.value[1]-r, self.point_get.value[1]+r+1
            x, x_1 = x[0], x_1[0]
            y, y_1 = y[0], y_1[0]
            if y < 0:
                y = 0
            if x < 0:
                x = 0
            if y_1 > shape[-2]:
                y_1 = shape[-2]
            if x_1 > shape[-1]:
                x_1 = shape[-1]
        
        # Update domain variable for where we will add data
        domain = self.local.variables['domain']
        if self.low_memory:
            for z in range(shape[1]):
                if z + 1 > shape[1] - 1:
                    z_1 = shape[1]
                else:
                    z_1 = z + 1
                if len(shape) == 4:
                    domain[time:time_1, z:z_1, y:y_1, x:x_1] = np.ones((time_1-time, z_1-z, y_1-y, x_1-x))
                elif len(shape) == 3:
                    if z == self.inds[0]:
                        domain[time:time_1, y:y_1, x:x_1] = np.ones((time_1-time, y_1-y, x_1-x))
        else:
            if len(shape) == 4:
                domain[inds[0]:inds[-1]+1, 0:shape[1], y:y_1, x:x_1] = np.ones((inds[-1]+1-inds[0], shape[1], y_1-y, x_1-x))
            elif len(shape) == 3:
                domain[inds[0]:inds[-1]+1, y:y_1, x:x_1] = np.ones((inds[-1]+1-inds[0], y_1-y, x_1-x))
        
        # Update the local variables with remove data              
        for local, remote in zip(localvars, remotevars):
            if self.low_memory:
                for z in range(shape[1]):
                    if z + 1 > shape[1] - 1:
                        z_1 = shape[1]
                    else:
                        z_1 = z + 1
                    if len(shape) == 4:
                        local[time:time_1, z:z_1, y:y_1, x:x_1] = remote[time:time_1,  z:z_1, y:y_1, x:x_1]
                    else:
                        if z == 0:
                            local[time:time_1, y:y_1, x:x_1] = remote[time:time_1, y:y_1, x:x_1]
           
            else:
                #print "time", inds, "rem", shape[1], y, y_1, x, x_1
                if len(shape) == 4:
                    local[inds[0]:inds[-1]+1, 0:shape[1], y:y_1, x:x_1] = remote[inds[0]:inds[-1]+1,  0:shape[1], y:y_1, x:x_1]
                else:
                    local[inds[0]:inds[-1]+1, y:y_1, x:x_1] = remote[inds[0]:inds[-1]+1, y:y_1, x:x_1]

    def __call__(self, proc):
        c = 0
        self.dataset = CommonDataset(self.url)
        self.proc = proc
        self.get_variablenames_for_model()
        self.remote = self.dataset.nc
        cachepath = self.cache_path
        times = self.times
        start_time = self.start_time
        
        # Calculate the datetimes of the model timesteps like
        # the particle objects do, so we can figure out unique
        # time indices
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
        
        # While there is at least 1 particle still running, 
        # stay alive, if not break
        while self.n_run.value > 1:
            # If particle asks for data, do the following
            if self.get_data.value == True:
                if c == 0:
                    indices = self.dataset.get_indices(self.uname, timeinds=[np.asarray([0])], point=self.start)
                    self.point_get.value = [self.inds[0], indices[-2], indices[-1]]
                    
                    # Set shared state so particles know the 
                    # cache is being updated
                    self.updating.value = True
                    
                    # Wait for particles to get out
                    while self.particle_get == True:
                        pass
                    
                    # Open local cache for writing, overwrites
                    # existing file with same name
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
                    
                    # Create domain variable that specifies
                    # where there is data geographically/by time
                    # and where there is not data,
                    #   Used for testing if particle needs to 
                    #   ask cache to update
                    domain = self.local.createVariable('domain',
                            'i', dimensions, zlib=False, fill_value=0,
                            )
                    domain.coordinates = coordinates
                            
                    if fill == None:
                        # Create local u and v variables
                        u = self.local.createVariable('u', 
                            'f', dimensions, zlib=False,
                            )
                        v = self.local.createVariable('v', 
                            'f', dimensions, zlib=False,
                            )
                        
                        v.coordinates = coordinates
                        u.coordinates = coordinates
                        
                        # Create local w variable
                        if self.wname != None:
                            w = self.local.createVariable('w', 
                                'f', dimensions, zlib=False,
                                )
                            w.coordinates = coordinates
                        if self.temp_name != None and self.salt_name != None:      
                            # Create local temp and salt vars  
                            temp = self.local.createVariable('temp', 
                                'f', dimensions, zlib=False,
                                )
                            salt = self.local.createVariable('salt', 
                                'f', dimensions, zlib=False,
                                )
                            temp.coordinates = coordinates
                            salt.coordinates = coordinates
                    else:    
                        # Create local u and v variables
                        u = self.local.createVariable('u', 
                            'f', dimensions, zlib=False,
                            fill_value=fill)
                        v = self.local.createVariable('v', 
                            'f', dimensions, zlib=False,
                            fill_value=fill)
                        
                        v.coordinates = coordinates
                        u.coordinates = coordinates
                        
                        # Create local w variable
                        if self.wname != None:
                            w = self.local.createVariable('w', 
                                'f', dimensions, zlib=False,
                                fill_value=fill)
                            w.coordinates = coordinates
                        if self.temp_name != None and self.salt_name != None: 
                            # Create local temp and salt vars       
                            temp = self.local.createVariable('temp', 
                                'f', dimensions, zlib=False,
                                fill_value=fill)
                            salt = self.local.createVariable('salt', 
                                'f', dimensions, zlib=False,
                                fill_value=fill)
                            temp.coordinates = coordinates
                            salt.coordinates = coordinates
                    
                    # Create local lat/lon coordinate variables
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
                        
                    # Create local z variable
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
                            
                    # Create local time variable
                    time = self.local.createVariable('time',
                                'f8', ("time",), zlib=False,
                                )
                    if self.tname != None:
                        time[:] = self.remote.variables[self.tname][self.inds]
                    
                    if self.point_get.value[0]+self.time_size > np.max(self.inds):
                        current_inds = np.arange(self.point_get.value[0], np.max(self.inds)+1)
                    else:
                        current_inds = np.arange(self.point_get.value[0],self.point_get.value[0] + self.time_size)
                    
                    # Get data from remote dataset and add
                    # to local cache  
                    self.get_remote_data(localvars, remotevars, current_inds, shape) 
                    
                    self.local.sync()
                    self.local.close()
                    c += 1

                    self.updating.value = False
                    self.get_data.value = False

                else:
                    #print "updating appending"
                    self.updating.value = True
                    # Wait for particles to get out (this is
                    # poorly implemented)
                    while self.particle_get == True:
                        pass
                        
                    # Open local cache dataset for appending
                    self.local = netCDF4.Dataset(cachepath, 'a')
                    
                    # Create local and remote variable objects
                    # for the variables of interest  
                    u = self.local.variables['u']
                    v = self.local.variables['v']
                    time = self.local.variables['time']
                    remoteu = self.remote.variables[self.uname]
                    remotev = self.remote.variables[self.vname]
                    
                    # Create lists of variable objects for
                    # the data updater
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
                    
                    if self.point_get.value[0]+self.time_size > np.max(self.inds):
                        current_inds = np.arange(self.point_get.value[0], np.max(self.inds)+1)
                    else:
                        current_inds = np.arange(self.point_get.value[0],self.point_get.value[0] + self.time_size)
                    
                    # Get data from remote dataset and add
                    # to local cache
                    self.get_remote_data(localvars, remotevars, current_inds, shape)
                    
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

    def __init__(self, part, remotehydro, times, start_time, models, 
                 point, usebathy, useshore, usesurface,
                 get_data, n_run, updating, particle_get,
                 point_get, request_lock, cache=None):
        """
            This is the task/class/object/job that forces an
            individual particle and communicates with the 
            other particles and data controller for local
            cache updates
        """
        assert cache != None
        self.cache_path = cache
        self.remotehydropath = remotehydro
        self.localpath =  self.cache_path
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
        self.request_lock = request_lock
        
        
    def get_variablenames_for_model(self, dataset):
        # Use standard names to get variable names for required
        # model parameters
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
        
        # Get coordinate names based on u variable
        coords = dataset.get_coord_names(self.uname) 
        self.xname = coords['xname'] 
        self.yname = coords['yname']
        self.zname = coords['zname']
        self.tname = coords['tname']
        # Get salt and temp names from std names
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
        
    def need_data(self, i):
        """
            Method to test if cache contains the data that
            the particle needs
        """
        self.particle_get.value = True
        self.dataset.opennc()
        # Test if the cache has the data we need
        try:
            # If the point we request contains fill values, 
            # we need data
            if type(np.mean(np.mean(self.dataset.get_values('domain', timeinds=[np.asarray([i])], point=self.part.location )))) == np.ma.core.MaskedArray:
                need = True
            else:
                need = False
        except:
            # If the time index doesnt even exist, we need
            need = True
        self.dataset.closenc()
        self.particle_get.value = False
        #print self.proc, need
        return need # return true if need data or false if dont
      
    def data(self, i):
        """
            Method to streamline request for data from cache
        """
        while self.get_data.value == True:
            pass
        #print self.proc, "done waiting"
        if self.need_data(i):
            #print self.proc, "yes i do need data"
            # Acquire lock for asking for data
            self.request_lock.acquire()
            if self.need_data(i):
                # Open netcdf file on disk from commondataset
                self.dataset.opennc()
                # Get the indices for the current particle location
                indices = self.dataset.get_indices('u', timeinds=[np.asarray([i-1])], point=self.part.location )
                self.dataset.closenc()
                # Override the time
                self.point_get.value = [indices[0]+1, indices[-2], indices[-1]]
                # Request that the data controller update the cache
                self.get_data.value = True
                # Wait until the data controller is done
                while self.get_data.value == True:
                    pass 
            self.request_lock.release()
               
        # Announce that someone is getting data from the local
        self.particle_get.value = True
        # Open netcdf file on disk from commondataset
        self.dataset.opennc()
        # Grab data at time index closest to particle location
        u = np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location )))
        v = np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location )))
        # if there is vertical velocity inthe dataset, get it
        if 'w' in self.dataset.nc.variables:
            w = np.mean(np.mean(self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location )))
        else:
            w = 0.0
        # If there is salt and temp in the dataset, get it
        if self.temp_name != None and self.salt_name != None:
            temp = np.mean(np.mean(self.dataset.get_values('temp', timeinds=[np.asarray([i])], point=self.part.location )))
            salt = np.mean(np.mean(self.dataset.get_values('salt', timeinds=[np.asarray([i])], point=self.part.location )))
        
        # Check for nans that occur in the ocean (happens because
        # of model and coastline resolution mismatches)
        if np.isnan(u) or np.isnan(v) or np.isnan(w):
            # Take the mean of the closest 4 points
            # If this includes nan which it will, result is nan
            u = np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location, num=4)))
            v = np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location, num=4)))
            if 'w' in self.dataset.nc.variables:
                w = np.mean(np.mean(self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location, num=4)))
            else:
                w = 0.0
            if self.temp_name != None and self.salt_name != None:
                temp = np.mean(np.mean(self.dataset.get_values('temp', timeinds=[np.asarray([i])], point=self.part.location, num=4)))
                salt = np.mean(np.mean(self.dataset.get_values('salt', timeinds=[np.asarray([i])], point=self.part.location, num=4)))
        # If the final data results are nan, set velocities to zero
        # TODO: need to validate this implementation
        if np.isnan(u) or np.isnan(v) or np.isnan(w):
            u, v, w = 0.0, 0.0, 0.0
        self.dataset.closenc()
        self.particle_get.value = False
        if self.temp_name != None and self.salt_name != None:
            return u, v, w, temp, salt
        else:
            return u,v,w, None, None
        
    def __call__(self, proc):
        if self.usebathy == True:
            self._bathymetry = Bathymetry(point=self.point)
        else:
            self._bathymetry = None
        if self.useshore == True:
            self._shoreline = Shoreline(point=self.point)
        else:
            self._shoreline = None
        self.proc = proc
        part = self.part
        times = self.times
        start_time = self.start_time
        models = self.models
        
        while self.get_data.value == True:
            pass
        # Initialize commondataset of local cache, then
        # close the related netcdf file
        self.dataset = CommonDataset(self.localpath)
        self.dataset.closenc()
        
        # Calculate datetime at every timestep
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
        
        # Get variable names for parameters required by model
        remote = CommonDataset(self.remotehydropath)
        self.get_variablenames_for_model(remote)

        # Figure out indices corresponding to timesteps
        timevar = remote.gettimevar(self.uname)
        time_indexs = timevar.nearest_index(newtimes)
        array_indexs = time_indexs - time_indexs[0]

        # loop over timesteps   
        for loop_i, i in enumerate(time_indexs):
     
            #queue_logger.logger().info("Particle %i at %s" % (part.id, newtimes[loop_i].isoformat()))

            newloc = None
            
            
            # Get data from local netcdf here
            # dataset = CommonDataset(".cache/localcache.nc")
            
            # if need a time that is outside of what we have:e
            while self.get_data.value == True:
                pass
                
            # Get the variable data required by the models
            u, v, w, temp, salt = self.data(i)

            # Age the particle by the modelTimestep (seconds)
            # 'Age' meaning the amount of time it has been forced.
            part.age(seconds=modelTimestep[loop_i])

            # loop over models - sort these in the order you want them to run
            for model in models:
                movement = model.move(part, u, v, w, modelTimestep[loop_i], temperature=temp, salinity=salt)
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
                hitpoint = Location4D(point=intersection_point['point'], time=starting.time + (ending.time - starting.time))
                particle.location = hitpoint
                particle.fill_location_gap()
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
    
