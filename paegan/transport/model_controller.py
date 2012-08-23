import unittest
import time
import matplotlib
import matplotlib.pyplot
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import netCDF4
from datetime import datetime
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import LarvaParticle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from paegan.utils.asatransport import AsaTransport
from paegan.transport.shoreline import Shoreline
from paegan.transport.bathymetry import Bathymetry
from shapely.geometry import Point, Polygon, MultiPolygon, MultiPoint, LineString
from shapely.geometry import MultiLineString
from multiprocessing import Value
import multiprocessing
from paegan.logging.null_handler import NullHandler
import paegan.transport.parallel_manager as parallel
import os
import uuid
from paegan.external import shapefile as shp
from shapely.ops import cascaded_union
from shapely.geometry import mapping
import json

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
                "\nuse_shoreline: " + str(self.use_shoreline)

    def generate_map(self, point):
        fig = matplotlib.pyplot.figure(figsize=(20,16)) # call a blank figure
        ax = fig.gca(projection='3d') # line with points
        
        tracks = []

        #for x in range(len(arr)):
        for particle in self.particles:
            tracks.append(particle.linestring())
            p_proj_lats = map(lambda la: la.latitude, particle.locations)
            p_proj_lons = map(lambda lo: lo.longitude, particle.locations)
            p_proj_depths = map(lambda dp: dp.depth, particle.locations)

            ax.plot(p_proj_lons, p_proj_lats, p_proj_depths, marker='o', c='red') # particles

        #add shoreline
        #tracks = MultiLineString(tracks)
        midpoint = point#tracks.centroid

        #bbox = tracks.bounds
        visual_bbox = (point.x-1.5, point.y-1.5, point.x+1.5, point.y+1.5)#tracks.buffer(1).bounds

        #max_distance = max(abs(bbox[0] - bbox[2]), abs(bbox[1] - bbox[3])) + 0.25

        coast_line = Shoreline(point=midpoint, spatialbuffer=1.5).linestring

        c_lons, c_lats = coast_line.xy
        c_lons = np.array(c_lons)
        c_lats = np.array(c_lats)
        c_lons = np.where((c_lons >= visual_bbox[0]) & (c_lons <= visual_bbox[2]), c_lons, np.nan)
        c_lats = np.where((c_lats >= visual_bbox[1]) & (c_lats <= visual_bbox[3]), c_lats, np.nan)

        #add bathymetry
        nc1 = netCDF4.Dataset(os.path.normpath(os.path.join(__file__,"../../resources/bathymetry/ETOPO1_Bed_g_gmt4.grd")))
        x = nc1.variables['x']
        y = nc1.variables['y']

        x_indexes = np.where((x[:] >= visual_bbox[0]) & (x[:] <= visual_bbox[2]))[0]
        y_indexes = np.where((y[:] >= visual_bbox[1]) & (y[:] <= visual_bbox[3]))[0]

        x_min = x_indexes[0] 
        x_max = x_indexes[-1]
        y_min = y_indexes[0]
        y_max = y_indexes[-1]

        lons = x[x_min:x_max]
        lats = y[y_min:y_max]
        bath = nc1.variables['z'][y_min:y_max,x_min:x_max]

        x_grid, y_grid = np.meshgrid(lons, lats)

        mpl_extent = matplotlib.transforms.Bbox.from_extents(visual_bbox[0],visual_bbox[1],visual_bbox[2],visual_bbox[3])
        
        ax.plot_surface(x_grid,y_grid,bath, rstride=1, cstride=1,
            cmap="gist_earth", shade=True, linewidth=0, antialiased=False,
            edgecolors=None) # bathymetry

        ax.plot(c_lons, c_lats, clip_box=mpl_extent, clip_on=True, color='c') # shoreline
        ax.set_xlim3d(visual_bbox[0],visual_bbox[2])
        ax.set_ylim3d(visual_bbox[1],visual_bbox[3])
        ax.set_zmargin(0.1)
        ax.view_init(85, -90)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_zlabel('Depth (m)')
        matplotlib.pyplot.show()
        return fig

    def run(self, hydrodataset, **kwargs):

        if self.start == None:
            raise TypeError("must provide a start time to run the models")

        # Calculate the model timesteps
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
        nproc = multiprocessing.cpu_count()
        request_lock = mgr.Lock()
        nproc_lock = mgr.Lock()
        
        # Create the task and result queues
        tasks = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()
        
        # Create the shared state objects
        get_data = mgr.Value('bool', True)
        n_run = mgr.Value('int', nproc)
        updating = mgr.Value('bool', False)
        particle_get = mgr.Value('bool', False)
        point_get = mgr.Value('list', [0, 0, 0])
        
        # Create workers
        procs = [ parallel.Consumer(tasks, results, n_run, nproc_lock)
                  for i in xrange(nproc) ]
        
        # Start workers
        logger.debug('Starting workers')
        for w in procs:
            w.start()
        
        # Generate temp filename for dataset cache
        temp_name = unique_filename(prefix=str(datetime.now().microsecond), suffix=".nc")
        self.cache_path = os.path.join(self.cache_path, temp_name)
        
        # Add data controller to the queue first so that it 
        # can get the initial data and is not blocked
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
                                            cache=self.cache_path))
        [tasks.put(None) for i in xrange(nproc)]

        # Wait for all tasks to finish
        tasks.join()
        
        # Get results back from queue, test for failed particles
        for i,v in enumerate(self.particles):
            tempres = results.get()
            self.particles[i] = tempres
            # Don't save failed particles
            while tempres == None or tempres == -1:
                if tempres == -1:
                    logger.warn('A particle failed!  Please check log file!')  
                tempres = results.get()
                self.particles[i] = tempres

        logger.debug('Workers complete')

        # Remove the cache file
        os.remove(self.cache_path)

        # If output_formats and path specified,
        # output particle run data to disk when completed
        if "output_formats" in kwargs:
            # Make sure output_path is also included
            if kwargs.get("output_path", None) != None:
                formats = kwargs.get("output_formats")
                output_path = kwargs.get("output_path")
                if isinstance(formats, list):
                    for form in formats:
                        filename = os.path.join(output_path,'model_run_output')
                        filename = filename + '.' + form.replace('.','')
                        self.export(filename)
                else:
                    logger.warn('The output_formats parameter should be a list, not saving any output!')  
            else:
                logger.warn('No output path defined, not saving any output!')  
        else:
            logger.warn('No output format defined, not saving any output!')
    
    def export(self, filepath, **kwargs):
        """
            General purpose export method, gets file type 
            from filepath extension
            
            Valid output formats currently are: * shp and nc *
        """
        if filepath[-3:] == "shp":
            self._export_shp(filepath)
        elif filepath[-2:] == "nc":
            self._export_nc(filepath)
        elif filepath[-4:] == "trkl":
            self._export_trackline(filepath)
            
    def _export_trackline(self, filepath):

        normalized_locations = [particle.noramlized_locations(self.datetimes) for particle in self.particles]

        track_coords = []
        for x in xrange(0, len(self.datetimes)):
            points = MultiPoint([loc[x].point.coords[0] for loc in normalized_locations])
            track_coords.append(points.centroid.coords[0])

        print track_coords
        ls = LineString(track_coords)
        open(filepath, "wb").write(json.dumps(mapping(ls)))

    def _export_shp(self, filepath):
        """
            Export particle data to point type shapefile
        """

        logger = multiprocessing.get_logger()
        logger.addHandler(NullHandler())

        # Create the shapefile writer
        w = shp.Writer(shp.POINT)
        # Create the attribute fields/columns
        w.field('Particle')
        w.field('Date')
        w.field('Lat')
        w.field('Lon')
        w.field('Depth')
        w.field('Temp')
        w.field('Salt')
        
        # Loop through locations in particles,
        # add as points to the shapefile
        for particle in self.particles:
            # If there was temperature and salinity in the model, and
            # we ran behaviors, the lengths should be the same

            normalized_locations = particle.noramlized_locations(self.datetimes)
            noramlized_temps = particle.noramlized_temps(self.datetimes)
            noramlized_salts = particle.noramlized_salts(self.datetimes)

            if len(normalized_locations) != len(noramlized_temps):
                logger.debug("No temperature being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                noramlized_temps = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(noramlized_salts):
                logger.debug("No salinity being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                noramlized_salts = [None] * len(normalized_locations)

            for loc, temp, salt in zip(normalized_locations, noramlized_temps, noramlized_salts):
                # Add point geometry
                w.point(loc.longitude, loc.latitude)
                # Add attribute records
                w.record(particle.uid, loc.time.isoformat(), loc.latitude, loc.longitude, loc.depth, temp, salt)

        # Write out shapefle to disk
        w.save(filepath, zipup=True)
        
    def _export_nc(self, filepath, **kwargs):
        """
            Export particle data to CF trajectory convention
            netcdf file
        """
        logger = multiprocessing.get_logger()
        logger.addHandler(NullHandler())
        
        time_units = 'seconds since 1990-01-01 00:00:00'
        
        # Create netcdf file, overwrite existing
        nc = netCDF4.Dataset(filepath, 'w')
        # Create netcdf dimensions
        nc.createDimension('time', None)
        nc.createDimension('particle', None)
        # Create netcdf variables
        time = nc.createVariable('time', 'f', ('time',))
        part = nc.createVariable('particle', 'i', ('particle',))
        depth = nc.createVariable('depth', 'f', ('time','particle'))
        lat = nc.createVariable('lat', 'f', ('time','particle'))
        lon = nc.createVariable('lon', 'f', ('time','particle'))
        salt = nc.createVariable('salt', 'f', ('time','particle'))
        temp = nc.createVariable('temp', 'f', ('time','particle'))
            
        # Loop through locations in each particle,
        # add to netcdf file
        for j, particle in enumerate(self.particles):
            part[j] = particle.uid
            i = 0

            normalized_locations = particle.noramlized_locations(self.datetimes)
            noramlized_temps = particle.noramlized_temps(self.datetimes)
            noramlized_salts = particle.noramlized_salts(self.datetimes)

            if len(normalized_locations) != len(noramlized_temps):
                logger.debug("No temperature being added to netcdf.")
                # Create list of 'None' equal to the length of locations
                noramlized_temps = [None] * len(normalized_locations)

            if len(normalized_locations) != len(noramlized_salts):
                logger.debug("No salinity being added to netcdf.")
                # Create list of 'None' equal to the length of locations
                noramlized_salts = [None] * len(normalized_locations)

            for loc, _temp, _salt in zip(normalized_locations, noramlized_temps, noramlized_salts):

                if j == 0:
                    time[i] = netCDF4.date2num(loc.time, time_units)
                depth[i, j] = loc.depth
                lat[i, j] = loc.latitude
                lon[i, j] = loc.longitude
                salt[i, j] = _salt
                temp[i, j] = _temp
                i += 1
        # Variable attributes
        depth.coordinates = "time particle lat lon"
        depth.standard_name = "depth_below_sea_surface"
        depth.units = "m"
        depth.POSITIVE = "up"
        depth.positive = "up"
        salt.coordinates = "time particle lat lon"
        salt.standard_name = "sea_water_salinity"
        salt.units = "psu"
        temp.coordinates = "time particle lat lon"
        temp.standard_name = "sea_water_temperature"
        temp.units = "degrees_C"
        time.units = time_units
        time.standard_name = "time"
        lat.units = "degrees_north"
        lon.units = "degrees_east"
        part.cf_role = "trajectory_id"
        
        # Global attributes
        nc.featureType = "trajectory"
        nc.summary = str(self)
        for key in kwargs:
            nc.__setattr__(key, kwargs.get(key))
        #nc.cdm_dataset_type = "trajectory"
        nc.sync()
        nc.close()
                
            
        
        
        
        

        
