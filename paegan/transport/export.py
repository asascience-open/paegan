import os
import multiprocessing
from shapely.geometry import Point, Polygon, MultiPolygon, MultiPoint, LineString
from paegan.logging.null_handler import NullHandler

# NetCDF
import netCDF4
import numpy as np

# Shapefile
from paegan.external import shapefile as shp

# Trackline
from shapely.geometry import mapping
import json

# Map2D
import matplotlib
import matplotlib.pyplot
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


class Export(object):
    @classmethod
    def export(cls, **kwargs):
        raise("Please implement the export method of your Export class.")

class Trackline(Export):
    @classmethod
    def export(cls, folder, particles, datetimes):
        """
            Export trackline data to GeoJSON file
        """
        normalized_locations = [particle.noramlized_locations(datetimes) for particle in particles]

        track_coords = []
        for x in xrange(0, len(datetimes)):
            points = MultiPoint([loc[x].point.coords[0] for loc in normalized_locations])
            track_coords.append(points.centroid.coords[0])

        ls = LineString(track_coords)

        filepath = os.path.join(folder, "trackline.geojson")
        open(filepath, "wb").write(json.dumps(mapping(ls)))
        return filepath

class Shapefile(Export):
    @classmethod
    def export(cls, folder, particles, datetimes):
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
        for particle in particles:
            # If there was temperature and salinity in the model, and
            # we ran behaviors, the lengths should be the same

            normalized_locations = particle.noramlized_locations(datetimes)
            noramlized_temps = particle.noramlized_temps(datetimes)
            noramlized_salts = particle.noramlized_salts(datetimes)

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

        filepath = os.path.join(folder, "shape.zip")
        # Write out shapefle to disk
        w.save(filepath, zipup=True)

class NetCDF(Export):
    @classmethod
    def export(cls, folder, particles, datetimes, summary, **kwargs):
        """
            Export particle data to CF trajectory convention
            netcdf file
        """
        logger = multiprocessing.get_logger()
        logger.addHandler(NullHandler())
        
        time_units = 'seconds since 1990-01-01 00:00:00'
        
        # Create netcdf file, overwrite existing
        filepath = os.path.join(folder,'trajectories.nc')
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
        for j, particle in enumerate(particles):
            part[j] = particle.uid
            i = 0

            normalized_locations = particle.noramlized_locations(datetimes)
            noramlized_temps = particle.noramlized_temps(datetimes)
            noramlized_salts = particle.noramlized_salts(datetimes)

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
        nc.summary = str(summary)
        for key in kwargs:
            nc.__setattr__(key, kwargs.get(key))
        #nc.cdm_dataset_type = "trajectory"
        nc.sync()
        nc.close()

class Map2D(Export):
    @classmethod
    def export(cls, folder, particles, midpoint):
        fig = matplotlib.pyplot.figure(figsize=(20,16)) # call a blank figure
        ax = fig.gca(projection='3d') # line with points
        
        tracks = []

        #for x in range(len(arr)):
        for particle in particles:
            tracks.append(particle.linestring())
            p_proj_lats = map(lambda la: la.latitude, particle.locations)
            p_proj_lons = map(lambda lo: lo.longitude, particle.locations)
            p_proj_depths = map(lambda dp: dp.depth, particle.locations)

            ax.plot(p_proj_lons, p_proj_lats, p_proj_depths, marker='o', c='red') # particles

        visual_bbox = (midpoint.x-1.5, midpoint-1.5, midpoint.x+1.5, midpoint.y+1.5)
        coast_line = Shoreline(point=midpoint, spatialbuffer=1.5).linestring

        c_lons, c_lats = coast_line.xy
        c_lons = np.array(c_lons)
        c_lats = np.array(c_lats)
        c_lons = np.where((c_lons >= visual_bbox[0]) & (c_lons <= visual_bbox[2]), c_lons, np.nan)
        c_lats = np.where((c_lats >= visual_bbox[1]) & (c_lats <= visual_bbox[3]), c_lats, np.nan)

        #add bathymetry
        nc1 = netCDF4.Dataset(os.path.normpath(os.path.join(__file__,"..","..","resources/bathymetry/ETOPO1_Bed_g_gmt4.grd")))
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