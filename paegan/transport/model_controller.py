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
from paegan.logging.null_handler import NullHandler
import cPickle as pickle
import tempfile

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
        self.start = kwargs.pop('start', None)
        self._step = kwargs.pop('step', 3600)
        self._models = kwargs.pop('models', None)
        self._dirty = True

        self.particles = []
        self._time_chunk = kwargs.get('time_chunk', 10)
        self._horiz_chunk = kwargs.get('horiz_chunk', 5)
        self.time_method = kwargs.get('time_method', 'interp')
        self.shore_path = None
        self.shoreline_path = kwargs.get("shoreline_path", None)

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

        logger = multiprocessing.get_logger()
        logger.addHandler(NullHandler())

        # Add ModelController description to logfile
        logger.info(self)

        # Add the model descriptions to logfile
        for m in self._models:
            logger.info(m)

        if self.start == None:
            raise TypeError("must provide a start time to run the models")

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
        
        logger.debug('Setting up particle start locations')
        point_locations = []
        if isinstance(self.geometry, Point):
            point_locations = [self.reference_location] * self._npart
        elif isinstance(self.geometry, Polygon) or isinstance(self.geometry, MultiPolygon):
            point_locations = [Location4D(latitude=loc.y, longitude=loc.x, depth=self._depth, time=self.start) for loc in AsaTransport.fill_polygon_with_points(goal=self._npart, polygon=self.geometry)]

        # Initialize the particles
        logger.debug('Initializing particles')
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
        read_count = mgr.Value('int', 0)

        # When something is writing to the cache file
        write_lock = mgr.Lock()

        point_get = mgr.Value('list', [0, 0, 0])
        active = mgr.Value('bool', True)
        
        try:
            ds = CommonDataset.open(hydrodataset)
            # Query the dataset for common variable names
            # and the time variable.
            logger.info("Retrieving variable information from dataset")
            common_variables = self.get_common_variables_from_dataset(ds)

            logger.info("Pickling time variable to disk for particles")
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
        
        data_controller = parallel.DataController(hydrodataset, common_variables, n_run, get_data, write_lock, read_lock, read_count,
                                                  time_chunk, horiz_chunk, times,
                                                  self.start, point_get, self.reference_location,
                                                  low_memory=low_memory,
                                                  cache=self.cache_path)
        tasks.put(data_controller)
        # Create DataController worker
        data_controller_process = parallel.Consumer(tasks, results, n_run, nproc_lock, active, get_data, write_lock, name="DataController")
        data_controller_process.start()
        logger.info('Started %s' % data_controller_process.name)

        logger.info('Adding %i particles as tasks' % len(self.particles))
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
                                        write_lock,
                                        read_lock,
                                        read_count,
                                        point_get,
                                        data_request_lock,
                                        bathy=self.bathy_path,
                                        shoreline_path=self.shoreline_path,
                                        cache=self.cache_path,
                                        time_method=self.time_method)
            tasks.put(forcing)

        # Create workers for the particles.
        procs = [ parallel.Consumer(tasks, results, n_run, nproc_lock, active, get_data, write_lock, name="ForceParticle-%d"%i)
                  for i in xrange(nproc - 1) ]
        for w in procs:
            w.start()
            logger.info('Started %s' % w.name)

        # Get results back from queue, test for failed particles
        return_particles = []
        retrieved = 0
        error_code = 0

        logger.info("Waiting for %i particle results" % len(self.particles))
        while retrieved < number_of_tasks:
            # Returns a tuple of code, result
            code, tempres = results.get()
            if code == None:
                logger.warn("Got an unrecognized response from a task.")
            elif code == -1:
                logger.info("Particle %s has FAILED!! Saving what was completed." % tempres.uid)
                return_particles.append(tempres)
            elif code == -2:
                error_code = code
                logger.info("DataController has FAILED!!  Removing cache file so the particles fail.")
                try:
                    os.remove(self.cache_path)
                except OSError:
                    logger.info("Could not remove cache file, it probably never existed")
                    pass
            elif isinstance(tempres, Particle):
                logger.info("Particle %d finished" % tempres.uid)
                return_particles.append(tempres)
            elif tempres == "DataController":
                logger.info("DataController finished")
            else:
                logger.info("Got a strange result on results queue")
                logger.info(str(tempres))

            retrieved += 1

            logger.info("Retrieved %i/%i results" % (retrieved,number_of_tasks))
        
        if len(return_particles) != len(self.particles):
            logger.warn("Some particles failed and are not included in the output")

        # The results queue should be empty at this point
        assert results.empty() is True

        # Should be good to join on the tasks now that the queue is empty
        tasks.join()
        data_controller_process.join()
        for w in procs:
            w.join()
        
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
                logger.info("Could not remove cache file, it probably never existed")

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
                                logger.info("Failed to export to: %s" % format)
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
        elif format == "slow_shape":
            ex.Shapefile.export(folder=folder_path, particles=self.particles, datetimes=self.datetimes)
        elif format == "netcdf" or format[-2:] == "nc":
            ex.NetCDF.export(folder=folder_path, particles=self.particles, datetimes=self.datetimes, summary=str(self))
