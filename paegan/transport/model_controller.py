import unittest
import time
from datetime import datetime
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import LarvaParticle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from paegan.utils.asatransport import AsaTransport
from paegan.transport.shoreline import Shoreline
from paegan.transport.bathymetry import Bathymetry
from shapely.geometry import Point, Polygon, MultiPolygon, LineString
from shapely.ops import cascaded_union
from multiprocessing import Value
import multiprocessing
import paegan.transport.parallel_manager as parallel
import os
import uuid 
import paegan.transport.export as ex
from paegan.logging.null_handler import NullHandler

def unique_filename(prefix=None, suffix=None):
    fn = []
    if prefix: fn.extend([prefix, '-'])
    fn.append(str(uuid.uuid4()))
    if suffix: fn.extend(['.', suffix.lstrip('.')])
    return ''.join(fn)

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
        self.depth = kwargs.pop('depth', 0)
        self.npart = kwargs.pop('npart', 1)
        self.start = kwargs.pop('start', None)
        self.step = kwargs.pop('step', 3600)
        self.models = kwargs.pop('models', None)
        self._dirty = True
        self._particles = []
        self._time_chunk = kwargs.get('time_chunk', 10)
        self._horiz_chunk = kwargs.get('horiz_chunk', 4)
        self.time_method = kwargs.get('time_method', 'interp')

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
            shore_geoms = Shoreline(point=c, spatialbuffer=spatialbuffer).geoms
            if len(shore_geoms) > 0:
                all_shore = cascaded_union(shore_geoms)
                geo = geo.difference(all_shore)

        self._geometry = geo
    def get_geometry(self):
        return self._geometry
    geometry = property(get_geometry, set_geometry)

    def get_reference_location(self):
        pt = self.geometry.centroid
        return Location4D(latitude=pt.y, longitude=pt.x, depth=self.depth, time=self.start)
    reference_location = property(get_reference_location, None)

    def set_depth(self, dep):
        self._depth = dep
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

    def set_use_seasurface(self, sea):
        self._use_seasurface = sea
    def get_use_seasurface(self):
        return self._use_seasurface
    use_seasurface = property(get_use_seasurface, set_use_seasurface)

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
                "\nstart_geometry: " + str(self.geometry) + \
                "\ndepth: " + str(self.depth) + \
                "\nstart: " + str(self.start) +\
                "\nstep: " + str(self.step) +\
                "\nnstep: " + str(self.nstep) +\
                "\nnpart: " + str(self.npart) +\
                "\nmodels: " + str(self.models) +\
                "\nuse_bathymetry: " + str(self.use_bathymetry) +\
                "\nuse_shoreline: " + str(self.use_shoreline) + \
                "\ntime_method: " + str(self.time_method)

    def run(self, hydrodataset, **kwargs):

        if self.start == None:
            raise TypeError("must provide a start time to run the models")

        # Calculate the model timesteps
        # We need times = len(self._nstep) + 1 since data is stored one timestep
        # after a particle is forced with the final timestep's data.
        times = range(0,(self._step*self._nstep)+1,self._step)
        # Calculate a datetime object for each model timestep
        # This method is duplicated in DataContoller and ForceParticle
        # using the 'times' variables above.  Will be useful in those other
        # locations for particles released at different times
        # i.e. released over a few days
        modelTimestep, self.datetimes = AsaTransport.get_time_objects_from_model_timesteps(times, start=self.start)

        time_chunk = self._time_chunk
        horiz_chunk = self._horiz_chunk
        hydrodataset = hydrodataset
        low_memory = kwargs.get("low_memory", False)
        self.cache_path = kwargs.get("cache",
                                os.path.join(os.path.dirname(__file__), "_cache"))
        
        logger = multiprocessing.get_logger()
        logger.addHandler(NullHandler())

        # Add ModelController description to logfile
        logger.info(self)

        logger.debug('Setting up particle start locations')
        point_locations = []
        if isinstance(self.geometry, Point):
            point_locations = [self.reference_location] * self._npart
        elif isinstance(self.geometry, Polygon) or isinstance(self.geometry, MultiPolygon):
            point_locations = [Location4D(latitude=loc.y, longitude=loc.x, depth=self.depth, time=self.start) for loc in AsaTransport.fill_polygon_with_points(goal=self._npart, polygon=self.geometry)]

        # Initialize the particles
        logger.debug('Initializing particles')
        for x in xrange(0, self._npart):
            p = LarvaParticle(id=x)
            p.location = point_locations[x]
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

        request_lock = mgr.Lock()
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
        particle_get = mgr.Value('bool', False)
        point_get = mgr.Value('list', [0, 0, 0])
        active = mgr.Value('bool', True)
        
        # Create workers
        procs = [ parallel.Consumer(tasks, results, n_run, nproc_lock, active, get_data)
                  for i in xrange(nproc) ]
        
        # Start workers
        logger.info('Starting %i workers' % len(procs))
        for w in procs:
            w.start()
        
        # Generate temp filename for dataset cache
        temp_name = unique_filename(prefix=str(datetime.now().microsecond), suffix=".nc")
        self.cache_path = os.path.join(self.cache_path, temp_name)
        
        # Add data controller to the queue first so that it 
        # can get the initial data and is not blocked
        logger.info('Adding DataController as task')
        tasks.put(parallel.DataController(
                  hydrodataset, n_run, get_data, updating,
                  time_chunk, horiz_chunk, particle_get, times,
                  self.start, point_get, self.reference_location,
                  low_memory=low_memory,
                  cache=self.cache_path))
               
	    # loop over particles
        for part in self.particles:
            tasks.put(parallel.ForceParticle(part, 
                                            hydrodataset,
                                            times, 
                                            self.start,
                                            self._models,
                                            self.reference_location.point,
                                            self._use_bathymetry,
                                            self._use_shoreline,
                                            self._use_seasurface,
                                            get_data,
                                            n_run,
                                            updating,
                                            particle_get,
                                            point_get,
                                            request_lock,
                                            cache=self.cache_path,
                                            time_method=self.time_method))

        logger.info('Adding %i particles as tasks' % len(self.particles))
        [tasks.put(None) for i in xrange(nproc)]
        
        # Get results back from queue, test for failed particles
        return_particles = []
        retrieved = 0
        logger.info("Waiting for %i particle results" % len(self.particles))
        while retrieved < len(self.particles):
            tempres = results.get()
            if tempres == None or tempres == -1:
                logger.info("Result not a particle")
            else:
                logger.info("Retrieving particle from result queue")
                return_particles.append(tempres)

            retrieved += 1

            logger.info("Retrieved %i results" % retrieved)
        
        if len(return_particles) != len(self.particles):
            logger.warn("Some particles failed and are not included in the output")

        self.particles = return_particles

        # The Data Controller is still on the queue, remove that
        logger.info("Waiting for DataController to finish")
        dc = results.get()
        logger.info("DataController finished")

        # Ther results queue should be empty at this point
        assert results.empty() is True

        logger.info("Clearing extra tasks from task queue")
        while True:
            try:
                tasks.task_done()
            except:
                logger.info("Queue clear")
                break

        # Should be good to join on the tasks now that the queue is empty
        tasks.join()
        
        logger.info('Workers complete')

        # Remove the cache file
        try:
            os.remove(self.cache_path)
        except:
            logger.info("Could not remove cache file, it probably never existed")
            pass


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
                            self.export(output_path, format=format)
                    else:
                        logger.warn('The output_formats parameter should be a list, not saving any output!')  
                else:
                    logger.warn('No output path defined, not saving any output!')  
            else:
                logger.warn('No output format defined, not saving any output!')
        else:
            logger.warn('No particles did anything, so not exporting anything')
    
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
            ex.Shapefile.export(folder=folder_path, particles=self.particles, datetimes=self.datetimes)
        elif format == "netcdf" or format[-2:] == "nc":
            ex.NetCDF.export(folder=folder_path, particles=self.particles, datetimes=self.datetimes, summary=str(self))
