import unittest
import numpy as np
import netCDF4
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from paegan.utils.asatransport import AsaTransport
from paegan.transport.shoreline import Shoreline
from paegan.transport.bathymetry import Bathymetry
from multiprocessing import Value
from paegan.cdm.dataset import CommonDataset
from paegan.cdm.timevar import date2num, num2date
import os, sys
import time as timer
import random
import math
import traceback
import Queue
import multiprocessing
import cPickle as pickle

from paegan.logger import logger

class Consumer(multiprocessing.Process):
    def __init__(self, task_queue, result_queue, n_run, nproc_lock, active, get_data, **kwargs):
        """
            This is the process class that does all the handling of queued tasks
        """
        multiprocessing.Process.__init__(self, **kwargs)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.n_run = n_run
        self.nproc_lock = nproc_lock
        self.active = active
        self.get_data = get_data
        
    def run(self):

        while True:

            try:
                next_task = self.task_queue.get(True, 10)
            except Queue.Empty:
                logger.info("No tasks left to complete, closing %s" % self.name)
                break
            else:
                answer = (None, None)
                try:
                    answer = (1, next_task(self.name, self.active))
                except Exception as detail:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    logger.error("Disabling Error: " +\
                                 repr(traceback.format_exception(exc_type, exc_value,
                                              exc_traceback)))
                    if isinstance(next_task, DataController):
                        answer = (-2, "DataController")
                        # Tell the particles that the DataController is releasing file
                        self.get_data.value = False
                        # The data controller has died, so don't process any more tasks
                        self.active.value = False
                    elif isinstance(next_task, ForceParticle):
                        answer = (-1, next_task.part)
                    else:
                        logger.warn("Strange task raised an exception: %s" % str(next_task.__class__))
                        answer = (None, None)
                finally:
                    self.result_queue.put(answer)

                    self.nproc_lock.acquire()
                    self.n_run.value = self.n_run.value - 1
                    self.nproc_lock.release()

                    self.task_queue.task_done()


class DataController(object):
    def __init__(self, url, common_variables, n_run, get_data, write_lock, has_write_lock, read_lock, read_count,
                 time_chunk, horiz_chunk, times,
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
        self.n_run = n_run
        self.get_data = get_data
        self.write_lock = write_lock
        self.has_write_lock = has_write_lock
        self.read_lock = read_lock
        self.read_count = read_count
        self.inds = None#np.arange(init_size+1)
        self.time_size = time_chunk
        self.horiz_size = horiz_chunk
        self.point_get = point_get
        self.low_memory = kwargs.get("low_memory", False)
        self.start_time = start_time
        self.times = times
        self.start = start

        # Set common variable names
        self.uname = common_variables.get("u", None)
        self.vname = common_variables.get("v", None)
        self.wname = common_variables.get("w", None)
        self.temp_name = common_variables.get("temp", None)
        self.salt_name = common_variables.get("salt", None)
        self.xname = common_variables.get("x", None)
        self.yname = common_variables.get("y", None)
        self.zname = common_variables.get("z", None)
        self.tname = common_variables.get("time", None)
    
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
        
        # Update the local variables with remote data
        logger.debug("Filling cache with: Time - %s:%s, Lat - %s:%s, Lon - %s:%s" % (str(inds[0]), str(inds[-1]+1), str(y), str(y_1), str(x), str(x_1)))
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
                if len(shape) == 4:
                    local[inds[0]:inds[-1]+1, 0:shape[1], y:y_1, x:x_1] = remote[inds[0]:inds[-1]+1,  0:shape[1], y:y_1, x:x_1]
                else:
                    local[inds[0]:inds[-1]+1, y:y_1, x:x_1] = remote[inds[0]:inds[-1]+1, y:y_1, x:x_1]

    def __call__(self, proc, active):
        c = 0
        
        self.dataset = CommonDataset.open(self.url)
        self.proc = proc
        self.remote = self.dataset.nc
        cachepath = self.cache_path
        
        # Calculate the datetimes of the model timesteps like
        # the particle objects do, so we can figure out unique
        # time indices
        modelTimestep, newtimes = AsaTransport.get_time_objects_from_model_timesteps(self.times, start=self.start_time)

        timevar = self.dataset.gettimevar(self.uname)

        # Don't need to grab the last datetime, as it is not needed for forcing, only
        # for setting the time of the final particle forcing
        time_indexs = timevar.nearest_index(newtimes[0:-1], select='before')
        
        # Have to make sure that we get the plus 1 for the
        # linear interpolation of u,v,w,temp,salt
        self.inds = np.unique(time_indexs)
        self.inds = np.append(self.inds, self.inds.max()+1)
        
        # While there is at least 1 particle still running, 
        # stay alive, if not break
        while self.n_run.value > 1:
            logger.debug("Particles are still running, waiting for them to request data...")
            timer.sleep(2)
            # If particle asks for data, do the following
            if self.get_data.value == True:
                logger.debug("Particle asked for data!")

                # Wait for particles to get out
                while True:
                    self.read_lock.acquire()

                    logger.debug("Read count: %d" % self.read_count.value)
                    if self.read_count.value > 0:
                        logger.debug("Waiting for write lock on cache file (particles must stop reading)...")
                        self.read_lock.release()
                        timer.sleep(4)
                    else:
                        break
                    
                # Get write lock on the file.  Already have read lock.
                self.write_lock.acquire()
                self.has_write_lock.value = os.getpid()

                if c == 0:
                    logger.debug("Creating cache file")
                    try:
                        # Open local cache for writing, overwrites
                        # existing file with same name
                        self.local = netCDF4.Dataset(cachepath, 'w')

                        indices = self.dataset.get_indices(self.uname, timeinds=[np.asarray([0])], point=self.start)
                        self.point_get.value = [self.inds[0], indices[-2], indices[-1]]
                        
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

                        # If there is no FillValue defined in the dataset, use np.nan. 
                        # Sometimes it will work out correctly and other times we will
                        # have a huge cache file.
                        try:
                            fill = self.remote.variables[self.uname].missing_value
                        except Exception:
                            fill = np.nan
                        
                        # Create domain variable that specifies
                        # where there is data geographically/by time
                        # and where there is not data,
                        #   Used for testing if particle needs to 
                        #   ask cache to update
                        domain = self.local.createVariable('domain', 'i', dimensions, zlib=False, fill_value=0)
                        domain.coordinates = coordinates
                                
                        # Create local u and v variables
                        u = self.local.createVariable('u', 'f', dimensions, zlib=False, fill_value=fill)
                        v = self.local.createVariable('v', 'f', dimensions, zlib=False, fill_value=fill)
                        
                        v.coordinates = coordinates
                        u.coordinates = coordinates

                        localvars = [u, v,]
                        remotevars = [self.remote.variables[self.uname], self.remote.variables[self.vname]]
                        
                        # Create local w variable
                        if self.wname != None:
                            w = self.local.createVariable('w', 'f', dimensions, zlib=False, fill_value=fill)
                            w.coordinates = coordinates
                            localvars.append(w)
                            remotevars.append(self.remote.variables[self.wname])

                        if self.temp_name != None and self.salt_name != None: 
                            # Create local temp and salt vars       
                            temp = self.local.createVariable('temp', 'f', dimensions, zlib=False, fill_value=fill)
                            salt = self.local.createVariable('salt', 'f', dimensions, zlib=False, fill_value=fill)
                            temp.coordinates = coordinates
                            salt.coordinates = coordinates
                            localvars.append(temp)
                            localvars.append(salt)
                            remotevars.append(self.remote.variables[self.temp_name])
                            remotevars.append(self.remote.variables[self.salt_name])
                        
                        # Create local lat/lon coordinate variables
                        if self.remote.variables[self.xname].ndim == 2:
                            lon = self.local.createVariable('lon', 'f', ("y", "x"), zlib=False)
                            lon[:] = self.remote.variables[self.xname][:, :]
                            lat = self.local.createVariable('lat', 'f', ("y", "x"), zlib=False)
                            lat[:] = self.remote.variables[self.yname][:, :]
                        if self.remote.variables[self.xname].ndim == 1:
                            lon = self.local.createVariable('lon', 'f', ("x"), zlib=False)
                            lon[:] = self.remote.variables[self.xname][:]
                            lat = self.local.createVariable('lat', 'f', ("y"), zlib=False)
                            lat[:] = self.remote.variables[self.yname][:]                           
                            
                        # Create local z variable
                        if self.zname != None:            
                            if self.remote.variables[self.zname].ndim == 4:
                                z = self.local.createVariable('z', 'f', ("time","level","y","x"), zlib=False)  
                                remotez = self.remote.variables[self.zname]
                                localvars.append(z)
                                remotevars.append(remotez)
                            elif self.remote.variables[self.zname].ndim == 3:
                                z = self.local.createVariable('z', 'f', ("level","y","x"), zlib=False)
                                z[:] = self.remote.variables[self.zname][:, :, :]
                            elif self.remote.variables[self.zname].ndim ==1:
                                z = self.local.createVariable('z', 'f', ("level",), zlib=False)
                                z[:] = self.remote.variables[self.zname][:]
                                
                        # Create local time variable
                        time = self.local.createVariable('time', 'f8', ("time",), zlib=False)
                        if self.tname != None:
                            time[:] = self.remote.variables[self.tname][self.inds]
                        
                        if self.point_get.value[0]+self.time_size > np.max(self.inds):
                            current_inds = np.arange(self.point_get.value[0], np.max(self.inds)+1)
                        else:
                            current_inds = np.arange(self.point_get.value[0],self.point_get.value[0] + self.time_size)
                        
                        # Get data from remote dataset and add
                        # to local cache  
                        while True:
                            try:
                                self.get_remote_data(localvars, remotevars, current_inds, shape)
                            except:
                                logger.warn("DataController failed to get remote data.  Trying again in 30 seconds")
                                timer.sleep(30)
                            else:
                                break
                        
                        c += 1
                    except StandardError:
                        logger.error("DataController failed to get data (first request)")
                        raise
                    finally:
                        self.local.sync()
                        self.local.close()
                        self.has_write_lock.value = -1
                        self.write_lock.release()
                        self.get_data.value = False
                        self.read_lock.release()
                        logger.debug("Done updating cache file, closing file, and releasing locks")
                else:
                    logger.debug("Updating cache file")
                    try:
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
                        while True:
                            try:
                                self.get_remote_data(localvars, remotevars, current_inds, shape)
                            except:
                                logger.warn("DataController failed to get remote data.  Trying again in 30 seconds")
                                timer.sleep(30)
                            else:
                                break
                        
                        c += 1
                    except StandardError:
                        logger.error("DataController failed to get data (not first request)")
                        raise
                    finally:
                        self.local.sync()
                        self.local.close()
                        self.has_write_lock.value = -1
                        self.write_lock.release()
                        self.get_data.value = False
                        self.read_lock.release()
                        logger.debug("Done updating cache file, closing file, and releasing locks")
            else:
                pass        

        self.dataset.closenc()

        return "DataController"

        
class ForceParticle(object):
    from paegan.transport.shoreline import Shoreline
    from paegan.transport.bathymetry import Bathymetry
    def __str__(self):
        return self.part.__str__()

    def __init__(self, part, remotehydro, common_variables, timevar_pickle_path, times, start_time, models, 
                 release_location_centroid, usebathy, useshore, usesurface,
                 get_data, n_run, read_lock, has_read_lock, read_count,
                 point_get, data_request_lock, has_data_request_lock, reverse_distance=None, bathy=None,
                 shoreline_path=None, cache=None, time_method=None):
        """
            This is the task/class/object/job that forces an
            individual particle and communicates with the 
            other particles and data controller for local
            cache updates
        """
        assert cache != None
        self.cache_path = cache
        self.bathy = bathy
        self.common_variables = common_variables
        self.localpath =  self.cache_path
        self.release_location_centroid = release_location_centroid
        self.part = part
        self.times = times
        self.start_time = start_time
        self.models = models
        self.usebathy = usebathy
        self.useshore = useshore
        self.usesurface = usesurface
        self.get_data = get_data
        self.n_run = n_run
        self.read_lock = read_lock
        self.has_read_lock = has_read_lock
        self.read_count = read_count
        self.point_get = point_get
        self.data_request_lock = data_request_lock
        self.has_data_request_lock = has_data_request_lock
        self.shoreline_path = shoreline_path
        self.timevar_pickle_path = timevar_pickle_path

        # Set common variable names
        self.uname = common_variables.get("u", None)
        self.vname = common_variables.get("v", None)
        self.wname = common_variables.get("w", None)
        self.temp_name = common_variables.get("temp", None)
        self.salt_name = common_variables.get("salt", None)
        self.xname = common_variables.get("x", None)
        self.yname = common_variables.get("y", None)
        self.zname = common_variables.get("z", None)
        self.tname = common_variables.get("time", None)

        self.reverse_distance = reverse_distance

        if time_method is None:
            time_method = 'interp'
        self.time_method = time_method
        
    def need_data(self, i):
        """
            Method to test if cache contains the data that
            the particle needs
        """

        logger.debug("Checking cache for data availability at %s." % self.part.location.logstring())

        try:
            # Tell the DataController that we are going to be reading from the file
            with self.read_lock:
                self.read_count.value += 1
                self.has_read_lock.append(os.getpid())

            self.dataset.opennc()
            # Test if the cache has the data we need
            # If the point we request contains fill values, 
            # we need data
            cached_lookup = self.dataset.get_values('domain', timeinds=[np.asarray([i])], point=self.part.location)
            logger.debug("Type of result: %s" % type(cached_lookup))
            logger.debug("Double mean of result: %s" % np.mean(np.mean(cached_lookup)))
            logger.debug("Type of Double mean of result: %s" % type(np.mean(np.mean(cached_lookup))))
            if type(np.mean(np.mean(cached_lookup))) == np.ma.core.MaskedConstant:
                need = True
                logger.debug("I NEED data.  Got back: %s" % cached_lookup)
            else:
                need = False
                logger.debug("I DO NOT NEED data")
        except StandardError:
            # If the time index doesnt even exist, we need
            need = True
            logger.debug("I NEED data (no time index exists in cache)")
        finally:
            self.dataset.closenc()
            with self.read_lock:
                self.read_count.value -= 1
                self.has_read_lock.remove(os.getpid())

        return need # return true if need data or false if dont
        
    def linterp(self, setx, sety, x):
        """
            Linear interp of model data values between time steps
        """
        if math.isnan(sety[0]) or math.isnan(setx[0]):
            return np.nan
        #if math.isnan(sety[0]):
        #    sety[0] = 0.
        #if math.isnan(sety[1]):
        #    sety[1] = 0.
        return sety[0] + (x - setx[0]) * ( (sety[1]-sety[0]) / (setx[1]-setx[0]) )
      
    def data_interp(self, i, timevar, currenttime):
        """
            Method to streamline request for data from cache,
            Uses linear interpolation bewtween timesteps to
            get u,v,w,temp,salt
        """
        if self.active.value == True:
            while self.get_data.value == True:
                logger.debug("Waiting for DataController to release cache file so I can read from it...")
                timer.sleep(4)
                pass

        if self.need_data(i+1):
            # Acquire lock for asking for data
            self.data_request_lock.acquire()
            self.has_data_request_lock.value = os.getpid()
            try:
                # Do I still need data?
                if self.need_data(i+1):

                    # Tell the DataController that we are going to be reading from the file
                    with self.read_lock:
                        self.read_count.value += 1
                        self.has_read_lock.append(os.getpid())

                    # Open netcdf file on disk from commondataset
                    self.dataset.opennc()
                    # Get the indices for the current particle location
                    indices = self.dataset.get_indices('u', timeinds=[np.asarray([i-1])], point=self.part.location )
                    self.dataset.closenc()

                    with self.read_lock:
                        self.read_count.value -= 1
                        self.has_read_lock.remove(os.getpid())
                    
                    # Override the time
                    # get the current time index data
                    self.point_get.value = [indices[0] + 1, indices[-2], indices[-1]]
                    # Request that the data controller update the cache
                    self.get_data.value = True
                    # Wait until the data controller is done
                    if self.active.value == True:
                        while self.get_data.value == True:
                            logger.debug("Waiting for DataController to update cache with the CURRENT time index")
                            timer.sleep(4)
                            pass 

                    # get the next time index data
                    self.point_get.value = [indices[0] + 2, indices[-2], indices[-1]]
                    # Request that the data controller update the cache
                    self.get_data.value = True
                    # Wait until the data controller is done
                    if self.active.value == True:
                        while self.get_data.value == True:
                            logger.debug("Waiting for DataController to update cache with the NEXT time index")
                            timer.sleep(4)
                            pass
            except StandardError:
                logger.warn("Particle failed to request data correctly")
                raise
            finally:
                # Release lock for asking for data
                self.has_data_request_lock.value = -1
                self.data_request_lock.release()
                

        # Tell the DataController that we are going to be reading from the file
        with self.read_lock:
            self.read_count.value += 1
            self.has_read_lock.append(os.getpid())

        try:
            # Open netcdf file on disk from commondataset
            self.dataset.opennc()

            # Grab data at time index closest to particle location
            u = [np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location ))),
                 np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i+1])], point=self.part.location )))]
            v = [np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location ))),
                 np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i+1])], point=self.part.location )))]
            # if there is vertical velocity inthe dataset, get it
            if 'w' in self.dataset.nc.variables:
                w = [np.mean(np.mean(self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location ))),
                    np.mean(np.mean(self.dataset.get_values('w', timeinds=[np.asarray([i+1])], point=self.part.location )))]
            else:
                w = [0.0, 0.0]
            # If there is salt and temp in the dataset, get it
            if self.temp_name != None and self.salt_name != None:
                temp = [np.mean(np.mean(self.dataset.get_values('temp', timeinds=[np.asarray([i])], point=self.part.location ))),
                        np.mean(np.mean(self.dataset.get_values('temp', timeinds=[np.asarray([i+1])], point=self.part.location )))]
                salt = [np.mean(np.mean(self.dataset.get_values('salt', timeinds=[np.asarray([i])], point=self.part.location ))),
                        np.mean(np.mean(self.dataset.get_values('salt', timeinds=[np.asarray([i+1])], point=self.part.location )))]
            
            # Check for nans that occur in the ocean (happens because
            # of model and coastline resolution mismatches)
            if np.isnan(u).any() or np.isnan(v).any() or np.isnan(w).any():
                # Take the mean of the closest 4 points
                # If this includes nan which it will, result is nan
                uarray1 = self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                varray1 = self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                uarray2 = self.dataset.get_values('u', timeinds=[np.asarray([i+1])], point=self.part.location, num=2)
                varray2 = self.dataset.get_values('v', timeinds=[np.asarray([i+1])], point=self.part.location, num=2)
                if 'w' in self.dataset.nc.variables:
                    warray1 = self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                    warray2 = self.dataset.get_values('w', timeinds=[np.asarray([i+1])], point=self.part.location, num=2)
                    w = [warray1.mean(), warray2.mean()]
                else:
                    w = [0.0, 0.0]
                    
                if self.temp_name != None and self.salt_name != None:
                    temparray1 = self.dataset.get_values('temp', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                    saltarray1 = self.dataset.get_values('salt', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                    temparray2 = self.dataset.get_values('temp', timeinds=[np.asarray([i+1])], point=self.part.location, num=2)
                    saltarray2 = self.dataset.get_values('salt', timeinds=[np.asarray([i+1])], point=self.part.location, num=2)
                    temp = [temparray1.mean(), temparray2.mean()]
                    salt = [saltarray1.mean(), saltarray2.mean()]
                u = [uarray1.mean(), uarray2.mean()]
                v = [varray1.mean(), varray2.mean()]             
            
            # Linear interp of data between timesteps
            currenttime = date2num(currenttime)
            timevar = timevar.datenum
            u = self.linterp(timevar[i:i+2], u, currenttime)
            v = self.linterp(timevar[i:i+2], v, currenttime)
            w = self.linterp(timevar[i:i+2], w, currenttime)
            if self.temp_name != None and self.salt_name != None:
                temp = self.linterp(timevar[i:i+2], temp, currenttime)
                salt = self.linterp(timevar[i:i+2], salt, currenttime)
            
            if self.temp_name is None:
                temp = np.nan
            if self.salt_name is None:
                salt = np.nan

            #logger.info(self.dataset.get_xyind_from_point('u', self.part.location, num=1))

        except StandardError:
            logger.error("Error in data_interp method on ForceParticle")
            raise
        finally:
            self.dataset.closenc()
            with self.read_lock:
                self.read_count.value -= 1
                self.has_read_lock.remove(os.getpid())

        return u, v, w, temp, salt
            
    def data_nearest(self, i, currenttime):
        """
            Method to streamline request for data from cache,
            Uses nearest time to get u,v,w,temp,salt
        """
        if self.active.value == True:
            while self.get_data.value == True:
                logger.debug("Waiting for DataController to release cache file so I can read from it...")
                timer.sleep(4)
                pass

        if self.need_data(i):
            # Acquire lock for asking for data
            self.data_request_lock.acquire()
            self.has_data_request_lock.value = os.getpid()
            try:
                if self.need_data(i):

                    with self.read_lock:
                        self.read_count.value += 1
                        self.has_read_lock.append(os.getpid())

                    # Open netcdf file on disk from commondataset
                    self.dataset.opennc()
                    # Get the indices for the current particle location
                    indices = self.dataset.get_indices('u', timeinds=[np.asarray([i-1])], point=self.part.location )
                    self.dataset.closenc()

                    with self.read_lock:
                        self.read_count.value -= 1
                        self.has_read_lock.remove(os.getpid())

                    # Override the time
                    self.point_get.value = [indices[0]+1, indices[-2], indices[-1]]
                    # Request that the data controller update the cache
                    # DATA CONTOLLER STARTS
                    self.get_data.value = True
                    # Wait until the data controller is done
                    if self.active.value == True:
                        while self.get_data.value == True:
                            logger.debug("Waiting for DataController to update cache...")
                            timer.sleep(4)
                            pass
            except StandardError:
                raise
            finally:
                self.has_data_request_lock.value = -1
                self.data_request_lock.release()

        # Tell the DataController that we are going to be reading from the file
        with self.read_lock:
            self.read_count.value += 1
            self.has_read_lock.append(os.getpid())

        try:
            # Open netcdf file on disk from commondataset
            self.dataset.opennc()

            # Grab data at time index closest to particle location
            u = np.mean(np.mean(self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location )))
            v = np.mean(np.mean(self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location )))
            # if there is vertical velocity inthe dataset, get it
            if 'w' in self.dataset.nc.variables:
                w = np.mean(np.mean(self.dataset.get_values('w', timeindsf=[np.asarray([i])], point=self.part.location )))
            else:
                w = 0.0
            # If there is salt and temp in the dataset, get it
            if self.temp_name != None and self.salt_name != None:
                temp = np.mean(np.mean(self.dataset.get_values('temp', timeinds=[np.asarray([i])], point=self.part.location )))
                salt = np.mean(np.mean(self.dataset.get_values('salt', timeinds=[np.asarray([i])], point=self.part.location )))
            
            # Check for nans that occur in the ocean (happens because
            # of model and coastline resolution mismatches)
            if np.isnan(u).any() or np.isnan(v).any() or np.isnan(w).any():
                # Take the mean of the closest 4 points
                # If this includes nan which it will, result is nan
                uarray1 = self.dataset.get_values('u', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                varray1 = self.dataset.get_values('v', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                if 'w' in self.dataset.nc.variables:
                    warray1 = self.dataset.get_values('w', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                    w = warray1.mean()
                else:
                    w = 0.0
                    
                if self.temp_name != None and self.salt_name != None:
                    temparray1 = self.dataset.get_values('temp', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                    saltarray1 = self.dataset.get_values('salt', timeinds=[np.asarray([i])], point=self.part.location, num=2)
                    temp = temparray1.mean()
                    salt = saltarray1.mean()
                u = uarray1.mean()
                v = varray1.mean()             
            
            if self.temp_name is None:
                temp = np.nan
            if self.salt_name is None:
                salt = np.nan

            #logger.info(self.dataset.get_xyind_from_point('u', self.part.location, num=1))

        except StandardError:
            logger.error("Error in data_nearest on ForceParticle")
            raise
        finally:
            self.dataset.closenc()
            with self.read_lock:
                self.read_count.value -= 1
                self.has_read_lock.remove(os.getpid())

        return u, v, w, temp, salt

        
    def __call__(self, proc, active):

        self.active = active

        if self.usebathy == True:
            self._bathymetry = Bathymetry(file=self.bathy)
        
        self._shoreline = None  
        if self.useshore == True:
            self._shoreline = Shoreline(file=self.shoreline_path, point=self.release_location_centroid, spatialbuffer=0.25)
            # Make sure we are not starting on land.  Raises exception if we are.
            self._shoreline.intersect(start_point=self.release_location_centroid, end_point=self.release_location_centroid)
            
        self.proc = proc
        part = self.part
        
        if self.active.value == True:
            while self.get_data.value == True:
                logger.debug("Waiting for DataController to start...")
                timer.sleep(10)
                pass

        # Initialize commondataset of local cache, then
        # close the related netcdf file
        try:
            with self.read_lock:
                self.read_count.value += 1
                self.has_read_lock.append(os.getpid())
            self.dataset = CommonDataset.open(self.localpath)
            self.dataset.closenc()
        except StandardError:
            logger.warn("No cache file: %s.  Particle exiting" % self.localpath)
            raise
        finally:
            with self.read_lock:
                self.read_count.value -= 1
                self.has_read_lock.remove(os.getpid())

        # Calculate datetime at every timestep
        modelTimestep, newtimes = AsaTransport.get_time_objects_from_model_timesteps(self.times, start=self.start_time)

        # Load Timevar from pickle serialization
        f = open(self.timevar_pickle_path,"rb")
        timevar = pickle.load(f)
        f.close()

        if self.time_method == 'interp':
            time_indexs = timevar.nearest_index(newtimes, select='before')
        elif self.time_method == 'nearest':
            time_indexs = timevar.nearest_index(newtimes)
        else:
            logger.warn("Method for computing u,v,w,temp,salt not supported!")
        try:
            assert len(newtimes) == len(time_indexs)
        except AssertionError:
            logger.error("Time indexes are messed up. Need to have equal datetime and time indexes")
            raise

        # loop over timesteps
        # We don't loop over the last time_index because
        # we need to query in the time_index and set the particle's
        # location as the 'newtime' object.
        for loop_i, i in enumerate(time_indexs[0:-1]):

            if self.active.value == False:
                raise ValueError("Particle exiting due to Failure.")

            newloc = None

            # if need a time that is outside of what we have
            #if self.active.value == True:
            #    while self.get_data.value == True:
            #        logger.info("Waiting for DataController to get out...")
            #        timer.sleep(4)
            #        pass
                
            # Get the variable data required by the models
            if self.time_method == 'nearest':
                u, v, w, temp, salt = self.data_nearest(i, newtimes[loop_i])
            elif self.time_method == 'interp': 
                u, v, w, temp, salt = self.data_interp(i, timevar, newtimes[loop_i])
            else:
                logger.warn("Method for computing u,v,w,temp,salt not supported!")

            #logger.info("U: %.4f, V: %.4f, W: %.4f" % (u,v,w))
            #logger.info("Temp: %.4f, Salt: %.4f" % (temp,salt))

            # Get the bathy value at the particles location
            if self.usebathy == True:
                bathymetry_value = self._bathymetry.get_depth(part.location)
            else:
                bathymetry_value = -999999999999999

            # Age the particle by the modelTimestep (seconds)
            # 'Age' meaning the amount of time it has been forced.
            part.age(seconds=modelTimestep[loop_i])

            # loop over models - sort these in the order you want them to run
            for model in self.models:
                movement = model.move(part, u, v, w, modelTimestep[loop_i], temperature=temp, salinity=salt, bathymetry_value=bathymetry_value)
                newloc = Location4D(latitude=movement['latitude'], longitude=movement['longitude'], depth=movement['depth'], time=newtimes[loop_i+1])
                logger.debug("%s - moved %.3f meters (horizontally) and %.3f meters (vertically) by %s with data from %s" % (part.logstring(), movement['distance'], movement['vertical_distance'], model.__class__.__name__, newtimes[loop_i].isoformat()))
                if newloc:
                    self.boundary_interaction(particle=part, starting=part.location, ending=newloc,
                        distance=movement['distance'], angle=movement['angle'], 
                        azimuth=movement['azimuth'], reverse_azimuth=movement['reverse_azimuth'], 
                        vertical_distance=movement['vertical_distance'], vertical_angle=movement['vertical_angle'])
                logger.debug("%s - was forced by %s and is now at %s" % (part.logstring(), model.__class__.__name__, part.location.logstring()))

            part.note = part.outputstring()
            # Each timestep, save the particles status and environmental variables.
            # This keep fields such as temp, salt, halted, settled, and dead matched up with the number of timesteps
            part.save()

        # We won't pull data for the last entry in locations, but we need to populate it with fill data.
        part.fill_environment_gap()

        if self.usebathy == True:
            self._bathymetry.close()

        if self.useshore == True:
            self._shoreline.close()

        return part
    
    def boundary_interaction(self, **kwargs):
        """
            Returns a list of Location4D objects
        """
        particle = kwargs.pop('particle')
        starting = kwargs.pop('starting')
        ending = kwargs.pop('ending')

        # shoreline
        if self.useshore:
            intersection_point = self._shoreline.intersect(start_point=starting.point, end_point=ending.point)
            if intersection_point:
                # Set the intersection point.
                hitpoint = Location4D(point=intersection_point['point'], time=starting.time + (ending.time - starting.time))
                particle.location = hitpoint

                # This relies on the shoreline to put the particle in water and not on shore.
                resulting_point = self._shoreline.react(start_point=starting,
                                              end_point=ending,
                                              hit_point=hitpoint,
                                              reverse_distance=self.reverse_distance,
                                              feature=intersection_point['feature'],
                                              distance=kwargs.get('distance'),
                                              angle=kwargs.get('angle'),
                                              azimuth=kwargs.get('azimuth'),
                                              reverse_azimuth=kwargs.get('reverse_azimuth'))
                ending.latitude = resulting_point.latitude
                ending.longitude = resulting_point.longitude
                ending.depth = resulting_point.depth
                logger.debug("%s - hit the shoreline at %s.  Setting location to %s." % (particle.logstring(), hitpoint.logstring(),  ending.logstring()))

        # bathymetry
        if self.usebathy:
            if not particle.settled:
                bintersect = self._bathymetry.intersect(start_point=starting, end_point=ending)
                if bintersect:
                    pt = self._bathymetry.react(type='reverse', start_point=starting, end_point=ending)
                    logger.debug("%s - hit the bottom at %s.  Setting location to %s." % (particle.logstring(), ending.logstring(), pt.logstring()))
                    ending.latitude = pt.latitude
                    ending.longitude = pt.longitude
                    ending.depth = pt.depth
                
        # sea-surface
        if self.usesurface:
            if ending.depth > 0:
                #logger.debug("%s - rose out of the water.  Setting depth to 0." % particle.logstring())
                ending.depth = 0

        particle.location = ending
        return
    
