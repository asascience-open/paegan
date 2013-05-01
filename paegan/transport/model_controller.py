import unittest
import time
from datetime import datetime
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import LarvaParticle
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from paegan.utils.asatransport import AsaTransport
from paegan.transport.shoreline import Shoreline
from paegan.transport.bathymetry import Bathymetry
from paegan.cdm.dataset import CommonDataset
from paegan.transport.exceptions import ModelError, DataControllerError
from shapely.geometry import Point, Polygon, MultiPolygon, LineString
from shapely.ops import cascaded_union
from multiprocessing import Value
import multiprocessing
import paegan.transport.parallel_manager as parallel
import os
import paegan.transport.export as ex
import cPickle as pickle
import tempfile
import Queue
import pytz

from paegan.logger import logger

class ModelController(object):
    """
        Controls the models
    """
    def __init__(self, **kwargs):

        """ 
            Mandatory named arguments:
            * geometry (Shapely Geometry Object) no default
            * depth (meters) default 0
            * start (DateTime Object) none
            * step (seconds) default 3600
            * npart (number of particles) default 1
            * nstep (number of steps) no default
            * models (list object) no default, so far there is a transport model and a behavior model
            geometry is interchangeable (if it is a point release) with:
            * latitude (DD) no default
            * longitude (DD) no default
            * depth (meters) default 0
        """

        # Dataset
        self._dataset = None

        # Defaults
        self._use_shoreline = kwargs.pop('use_shoreline', True)
        self._use_bathymetry = kwargs.pop('use_bathymetry', True)
        self._use_seasurface = kwargs.pop('use_seasurface', True)
        self._depth = kwargs.pop('depth', 0)
        self._npart = kwargs.pop('npart', 1)

        self.start = kwargs.pop('start')
        if self.start == None:
            raise TypeError("must provide a start time to run the model")

        # Always convert to UTC
        if self.start.tzinfo is None:
            self.start = self.start.replace(tzinfo=pytz.utc)
        self.start = self.start.astimezone(pytz.utc)

        self._step = kwargs.pop('step', 3600)
        self._models = kwargs.pop('models', None)
        self._dirty = True

        self.particles = []
        self._time_chunk = kwargs.get('time_chunk', 10)
        self._horiz_chunk = kwargs.get('horiz_chunk', 5)
        self.time_method = kwargs.get('time_method', 'interp')
        self.shoreline_path = kwargs.get("shoreline_path", None)

        self.reverse_distance = kwargs.get("reverse_distance", 100)

        # The model timesteps in datetime objects
        self.datetimes = []
        
        # Inerchangeables
        if "geometry" in kwargs:
            self.geometry = kwargs.pop('geometry')
            if not isinstance(self.geometry, Point) and not isinstance(self.geometry, Polygon) and not isinstance(self.geometry, MultiPolygon):
                raise TypeError("The geometry attribute must be a shapely Point or Polygon")
        elif "latitude" and "longitude" in kwargs:
            self.geometry = Point(kwargs.pop('longitude'), kwargs.pop('latitude'))
        else:
            raise TypeError("must provide a shapely geometry object (point or polygon) or a latitude and a longitude")

        # Errors
        if "nstep" in kwargs:
            self._nstep = kwargs.pop('nstep')
        else:
            raise TypeError("must provide the number of timesteps")

    def set_geometry(self, geo):
        # If polygon is passed in, we need to trim it by the coastline
        # so we don't start particles on land
        if isinstance(geo, Polygon) and self._use_shoreline:
            c = geo.centroid
            b = geo.bounds
            spatialbuffer = max(b[2] - b[0], b[3] - b[1])
            shore_geoms = Shoreline(file=self.shoreline_path, point=c, spatialbuffer=spatialbuffer).geoms
            if len(shore_geoms) > 0:
                all_shore = cascaded_union(shore_geoms)
                geo = geo.difference(all_shore)

        self._geometry = geo
    def get_geometry(self):
        return self._geometry
    geometry = property(get_geometry, set_geometry)

    def get_reference_location(self):
        pt = self.geometry.centroid
        return Location4D(latitude=pt.y, longitude=pt.x, depth=self._depth, time=self.start)
    reference_location = property(get_reference_location, None)

    def set_start(self, sta):
        self._start = sta
    def get_start(self):
        return self._start
    start = property(get_start, set_start)

    def set_particles(self, parts):
        self._particles = parts
    def get_particles(self):
        return self._particles
    particles = property(get_particles, set_particles)

    def __str__(self):
        return  """
            *** ModelController ***
              start_geometry: %s
              depth: %d
              start: %s
              timestep (seconds): %d
              steps: %d
              particles: %d
              bathymetry: %s
              shoreline: %s
              seasurface: %s
              time_method: %s
            """ % (str(self.geometry), self._depth, str(self.start), self._step, self._nstep, self._npart, self._use_bathymetry, self._use_shoreline, self._use_seasurface, self.time_method)

    def get_common_variables_from_dataset(self, dataset):

        def getname(name):
            nm = dataset.get_varname_from_stdname(name)
            if len(nm) > 0:
                return nm[0]
            else:
                return None

        uname = getname('eastward_sea_water_velocity') 
        vname = getname('northward_sea_water_velocity') 
        wname = getname('upward_sea_water_velocity')
        temp_name = getname('sea_water_temperature') 
        salt_name = getname('sea_water_salinity')

        coords = dataset.get_coord_names(uname) 
        xname = coords['xname'] 
        yname = coords['yname']
        zname = coords['zname']
        tname = coords['tname']
        tname = None ## temporary

        return {
            "u"     :   uname,
            "v"     :   vname,
            "w"     :   wname,
            "temp"  :   temp_name,
            "salt"  :   salt_name,
            "x"     :   xname,
            "y"     :   yname,
            "z"     :   zname,
            "time"  :   tname
        }

    def run(self, hydrodataset, **kwargs):

        # Add ModelController description to logfile
        logger.info(self)

        # Add the model descriptions to logfile
        for m in self._models:
            logger.info(m)

        # Calculate the model timesteps
        # We need times = len(self._nstep) + 1 since data is stored one timestep
        # after a particle is forced with the final timestep's data.
        times = range(0,(self._step*self._nstep)+1,self._step)
        # Calculate a datetime object for each model timestep
        # This method is duplicated in DataController and ForceParticle
        # using the 'times' variables above.  Will be useful in those other
        # locations for particles released at different times
        # i.e. released over a few days
        modelTimestep, self.datetimes = AsaTransport.get_time_objects_from_model_timesteps(times, start=self.start)

        time_chunk = self._time_chunk
        horiz_chunk = self._horiz_chunk
        low_memory = kwargs.get("low_memory", False)

        # Should we remove the cache file at the end of the run?
        remove_cache = kwargs.get("remove_cache", True)

        self.bathy_path = kwargs.get("bathy", None)

        self.cache_path = kwargs.get("cache", None)
        if self.cache_path is None:
            # Generate temp filename for dataset cache
            default_cache_dir = os.path.join(os.path.dirname(__file__), "_cache")
            temp_name = AsaRandom.filename(prefix=str(datetime.now().microsecond), suffix=".nc")
            self.cache_path = os.path.join(default_cache_dir, temp_name)
        
        logger.progress((1, "Setting up particle start locations"))
        point_locations = []
        if isinstance(self.geometry, Point):
            point_locations = [self.reference_location] * self._npart
        elif isinstance(self.geometry, Polygon) or isinstance(self.geometry, MultiPolygon):
            point_locations = [Location4D(latitude=loc.y, longitude=loc.x, depth=self._depth, time=self.start) for loc in AsaTransport.fill_polygon_with_points(goal=self._npart, polygon=self.geometry)]

        # Initialize the particles
        logger.progress((2, "Initializing particles"))
        for x in xrange(0, self._npart):
            p = LarvaParticle(id=x)
            p.location = point_locations[x]
            # We don't need to fill the location gaps here for environment variables
            # because the first data collected actually relates to this original
            # position.
            # We do need to fill in fields such as settled, halted, etc.
            p.fill_status_gap()
            # Set the inital note
            p.note = p.outputstring()
            p.notes.append(p.note)
            self.particles.append(p)

        # This is where it makes sense to implement the multiprocessing
        # looping for particles and models. Can handle each particle in 
        # parallel probably.
        #
        # Get the number of cores (may take some tuning) and create that
        # many workers then pass particles into the queue for the workers
        mgr = multiprocessing.Manager()
        nproc = multiprocessing.cpu_count() - 1
        if nproc <= 0:
            raise ValueError("Model does not run using less than two CPU cores")

        # Each particle is a task, plus the DataController
        number_of_tasks = len(self.particles) + 1

        # We need a process for each particle and one for the data controller
        nproc = min(number_of_tasks, nproc)

        # When a particle requests data
        data_request_lock = mgr.Lock()
        # PID of process with lock
        has_data_request_lock = mgr.Value('int',-1)

        nproc_lock = mgr.Lock()
        
        # Create the task queue for all of the particles and the DataController
        tasks = multiprocessing.JoinableQueue(number_of_tasks)
        # Create the result queue for all of the particles and the DataController
        results = mgr.Queue(number_of_tasks)
        
        # Create the shared state objects
        get_data = mgr.Value('bool', True)
        # Number of tasks
        n_run = mgr.Value('int', number_of_tasks)
        updating = mgr.Value('bool', False)

        # When something is reading from cache file
        read_lock = mgr.Lock()
        # list of PIDs that are reading
        has_read_lock = mgr.list()
        read_count = mgr.Value('int', 0)

        # When something is writing to the cache file
        write_lock = mgr.Lock()
        # PID of process with lock
        has_write_lock = mgr.Value('int',-1)

        point_get = mgr.Value('list', [0, 0, 0])
        active = mgr.Value('bool', True)
        
        logger.progress((3, "Initializing and caching hydro model's grid"))
        try:
            ds = CommonDataset.open(hydrodataset)
            # Query the dataset for common variable names
            # and the time variable.
            logger.debug("Retrieving variable information from dataset")
            common_variables = self.get_common_variables_from_dataset(ds)

            logger.debug("Pickling time variable to disk for particles")
            timevar = ds.gettimevar(common_variables.get("u"))
            f, timevar_pickle_path = tempfile.mkstemp()
            os.close(f)
            f = open(timevar_pickle_path, "wb")
            pickle.dump(timevar, f)
            f.close()
            ds.closenc()
        except:
            logger.warn("Failed to access remote dataset %s" % hydrodataset)
            raise DataControllerError("Inaccessible DAP endpoint: %s" % hydrodataset)


        # Add data controller to the queue first so that it 
        # can get the initial data and is not blocked
        
        logger.debug('Starting DataController')
        logger.progress((4, "Starting processes"))
        data_controller = parallel.DataController(hydrodataset, common_variables, n_run, get_data, write_lock, has_write_lock, read_lock, read_count,
                                                  time_chunk, horiz_chunk, times,
                                                  self.start, point_get, self.reference_location,
                                                  low_memory=low_memory,
                                                  cache=self.cache_path)
        tasks.put(data_controller)
        # Create DataController worker
        data_controller_process = parallel.Consumer(tasks, results, n_run, nproc_lock, active, get_data, name="DataController")
        data_controller_process.start()
        
        logger.debug('Adding %i particles as tasks' % len(self.particles))
        for part in self.particles:
            forcing = parallel.ForceParticle(part,
                                        hydrodataset,
                                        common_variables,
                                        timevar_pickle_path,
                                        times,
                                        self.start,
                                        self._models,
                                        self.reference_location.point,
                                        self._use_bathymetry,
                                        self._use_shoreline,
                                        self._use_seasurface,
                                        get_data,
                                        n_run,
                                        read_lock,
                                        has_read_lock,
                                        read_count,
                                        point_get,
                                        data_request_lock,
                                        has_data_request_lock,
                                        reverse_distance=self.reverse_distance,
                                        bathy=self.bathy_path,
                                        shoreline_path=self.shoreline_path,
                                        cache=self.cache_path,
                                        time_method=self.time_method)
            tasks.put(forcing)

        # Create workers for the particles.
        procs = [ parallel.Consumer(tasks, results, n_run, nproc_lock, active, get_data, name="ForceParticle-%d"%i)
                  for i in xrange(nproc - 1) ]
        for w in procs:
            w.start()
            logger.debug('Started %s' % w.name)

        # Get results back from queue, test for failed particles
        return_particles = []
        retrieved = 0.
        error_code = 0

        logger.info("Waiting for %i particle results" % len(self.particles))
        logger.progress((5, "Running model"))
        while retrieved < number_of_tasks:
            try:
                # Returns a tuple of code, result
                code, tempres = results.get(timeout=240)
            except Queue.Empty:
                # Poll the active processes to make sure they are all alive and then continue with loop
                if not data_controller_process.is_alive() and data_controller_process.exitcode != 0:
                    # Data controller is zombied, kill off other processes.
                    get_data.value == False
                    results.put((-2, "DataController"))

                new_procs = []
                old_procs = []
                for p in procs:
                    if not p.is_alive() and p.exitcode != 0:
                        # Do what the Consumer would do if something finished.
                        # Add something to results queue
                        results.put((-3, "ZombieParticle"))
                        # Decrement nproc (DataController exits when this is 0)
                        with nproc_lock:
                            n_run.value = n_run.value - 1

                        # Remove task from queue (so they can be joined later on)
                        tasks.task_done()

                        # Start a new Consumer.  It will exit if there are no tasks available.
                        np = parallel.Consumer(tasks, results, n_run, nproc_lock, active, get_data, name=p.name)
                        new_procs.append(np)
                        old_procs.append(p)
                        
                        # Release any locks the PID had
                        if p.pid in has_read_lock:
                            with read_lock:
                                read_count.value -= 1
                                has_read_lock.remove(p.pid)

                        if has_data_request_lock.value == p.pid:
                            has_data_request_lock.value = -1
                            try:
                                data_request_lock.release()
                            except:
                                pass
                            
                        if has_write_lock.value == p.pid:
                            has_write_lock.value = -1
                            try:
                                write_lock.release()
                            except:
                                pass
                            

                for p in old_procs:
                    try:
                        procs.remove(p)
                    except ValueError:
                        logger.warn("Did not find %s in the list of processes.  Continuing on." % p.name)

                for p in new_procs:
                    procs.append(p)
                    logger.warn("Started a new consumer (%s) to replace a zombie consumer" % p.name)
                    p.start()
                
            else:
                # We got one.
                retrieved += 1
                if code == None:
                    logger.warn("Got an unrecognized response from a task.")
                elif code == -1:
                    logger.warn("Particle %s has FAILED!!" % tempres.uid)
                elif code == -2:
                    error_code = code
                    logger.warn("DataController has FAILED!!  Removing cache file so the particles fail.")
                    try:
                        os.remove(self.cache_path)
                    except OSError:
                        logger.debug("Could not remove cache file, it probably never existed")
                        pass
                elif code == -3:
                    error_code = code
                    logger.info("A zombie process was caught and task was removed from queue")
                elif isinstance(tempres, Particle):
                    logger.info("Particle %d finished" % tempres.uid)
                    return_particles.append(tempres)
                    # We mulitply by 95 here to save 5% for the exporting
                    logger.progress((round((retrieved / number_of_tasks) * 90.,1), "Particle %d finished" % tempres.uid))
                elif tempres == "DataController":
                    logger.info("DataController finished")
                    logger.progress((round((retrieved / number_of_tasks) * 90.,1), "DataController finished"))
                else:
                    logger.info("Got a strange result on results queue")
                    logger.info(str(tempres))

                logger.info("Retrieved %i/%i results" % (int(retrieved),number_of_tasks))
        
        if len(return_particles) != len(self.particles):
            logger.warn("Some particles failed and are not included in the output")

        # The results queue should be empty at this point
        assert results.empty() is True

        # Should be good to join on the tasks now that the queue is empty
        logger.info("Joining the task queue")
        tasks.join()

        # Join all processes
        logger.info("Joining the processes")
        for w in procs + [data_controller_process]:
                # Wait 10 seconds
                w.join(10.)
                if w.is_alive():
                    # Process is hanging, kill it.
                    logger.info("Terminating %s forcefully.  This should have exited itself." % w.name)
                    w.terminate()
                    
        logger.info('Workers complete')

        self.particles = return_particles

        # Remove Manager so it shuts down
        del mgr

        # Remove pickled timevar
        os.remove(timevar_pickle_path)

        # Remove the cache file
        if remove_cache is True:
            try:
                os.remove(self.cache_path)
            except OSError:
                logger.debug("Could not remove cache file, it probably never existed")

        logger.progress((96, "Exporting results"))

        if len(self.particles) > 0:
            # If output_formats and path specified,
            # output particle run data to disk when completed
            if "output_formats" in kwargs:
                # Make sure output_path is also included
                if kwargs.get("output_path", None) != None:
                    formats = kwargs.get("output_formats")
                    output_path = kwargs.get("output_path")
                    if isinstance(formats, list):
                        for format in formats:
                            logger.info("Exporting to: %s" % format)
                            try:
                                self.export(output_path, format=format)
                            except:
                                logger.error("Failed to export to: %s" % format)
                    else:
                        logger.warn('The output_formats parameter should be a list, not saving any output!')  
                else:
                    logger.warn('No output path defined, not saving any output!')  
            else:
                logger.warn('No output format defined, not saving any output!')
        else:
            logger.warn("Model didn't actually do anything, check the log.")
            if error_code == -2:
                raise DataControllerError("Error in the DataController")
            else:
                raise ModelError("Error in the model")

        logger.progress((99, "Model Run Complete"))
        return
    
    def export(self, folder_path, format=None):
        """
            General purpose export method, gets file type 
            from filepath extension
            
            Valid output formats currently are:
                Trackline: trackline or trkl or *.trkl                
                Shapefile: shapefile or shape or shp or *.shp
                NetCDF:    netcdf or nc or *.nc
        """

        if format is None:
            raise ValueError("Must export to a specific format, no format specified.")

        format = format.lower()

        if format == "trackline" or format[-4:] == "trkl":
            ex.Trackline.export(folder=folder_path, particles=self.particles, datetimes=self.datetimes)
        elif format == "shape" or format == "shapefile" or format[-3:] == "shp":
            ex.GDALShapefile.export(folder=folder_path, particles=self.particles, datetimes=self.datetimes)
        elif format == "netcdf" or format[-2:] == "nc":
            ex.NetCDF.export(folder=folder_path, particles=self.particles, datetimes=self.datetimes, summary=str(self))
        elif format == "pickle" or format[-3:] == "pkl" or format[-6:] == "pickle":
            ex.Pickle.export(folder=folder_path, particles=self.particles, datetimes=self.datetimes)
