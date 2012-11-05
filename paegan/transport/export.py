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
        normalized_locations = [particle.normalized_locations(datetimes) for particle in particles]

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
        shape = shp.Writer(shp.POINT)
        # Create the attribute fields/columns
        shape.field('Particle')
        shape.field('Date')
        shape.field('Lat')
        shape.field('Lon')
        shape.field('Depth')
        shape.field('Temp')
        shape.field('Salt')
        shape.field('U')
        shape.field('V')
        shape.field('W')
        shape.field('Settled')
        shape.field('Dead')
        shape.field('Halted')
        shape.field('Notes')
        
        # Loop through locations in particles,
        # add as points to the shapefile
        for particle in particles:
            # If there was temperature and salinity in the model, and
            # we ran behaviors, the lengths should be the same
            normalized_locations = particle.normalized_locations(datetimes)
            normalized_temps = particle.temps
            normalized_salts = particle.salts
            normalized_u = particle.u_vectors
            normalized_v = particle.v_vectors
            normalized_w = particle.w_vectors
            normalized_settled = particle.settles
            normalized_dead = particle.deads
            normalized_halted = particle.halts
            normalized_notes = particle.notes

            if len(normalized_locations) != len(normalized_temps):
                logger.info("No temperature being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_temps = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_salts):
                logger.info("No salinity being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_salts = [None] * len(normalized_locations)

            if len(normalized_locations) != len(normalized_u):
                logger.info("No U being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_u = [None] * len(normalized_locations)

            if len(normalized_locations) != len(normalized_v):
                logger.info("No V being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_v = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_w):
                logger.info("No W being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_w = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_settled):
                logger.info("No Settled being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_settled = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_dead):
                logger.info("No Dead being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_dead = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_halted):
                logger.info("No Halted being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_halted = [None] * len(normalized_locations)

            if len(normalized_locations) != len(normalized_notes):
                logger.info("No Notes being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_notes = [None] * len(normalized_locations) 

            for loc, temp, salt, u, v, w, settled, dead, halted, note in zip(normalized_locations, normalized_temps, normalized_salts, normalized_u, normalized_v, normalized_w, normalized_settled, normalized_dead, normalized_halted, normalized_notes):
                # Add point geometry
                shape.point(loc.longitude, loc.latitude)
                # Add attribute records
                shape.record(particle.uid, loc.time.isoformat(), loc.latitude, loc.longitude, loc.depth, temp, salt, u, v, w, settled, dead, halted, note)
        filepath = os.path.join(folder, "shape.zip")
        # Write out shapefle to disk
        shape.save(filepath, zipup=True)

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
        u = nc.createVariable('u', 'f', ('time','particle'))
        v = nc.createVariable('v', 'f', ('time','particle'))
        w = nc.createVariable('w', 'f', ('time','particle'))
        settled = nc.createVariable('settled', 'f', ('time','particle'))
        dead = nc.createVariable('dead', 'f', ('time','particle'))
        halted = nc.createVariable('halted', 'f', ('time','particle'))
            
        # Loop through locations in each particle,
        # add to netcdf file
        for j, particle in enumerate(particles):
            part[j] = particle.uid
            i = 0

            normalized_locations = particle.normalized_locations(datetimes)
            normalized_temps = particle.temps
            normalized_salts = particle.salts
            normalized_u = particle.u_vectors
            normalized_v = particle.v_vectors
            normalized_w = particle.w_vectors
            normalized_settled = particle.settles
            normalized_dead = particle.deads
            normalized_halted = particle.halts

            if len(normalized_locations) != len(normalized_temps):
                logger.info("No temperature being added to netcdf.")
                # Create list of 'None' equal to the length of locations
                normalized_temps = [None] * len(normalized_locations)

            if len(normalized_locations) != len(normalized_salts):
                logger.info("No salinity being added to netcdf.")
                # Create list of 'None' equal to the length of locations
                normalized_salts = [None] * len(normalized_locations)

            if len(normalized_locations) != len(normalized_u):
                logger.info("No U being added to netcdf.")
                # Create list of 'None' equal to the length of locations
                normalized_u = [None] * len(normalized_locations)

            if len(normalized_locations) != len(normalized_v):
                logger.info("No V being added to netcdf.")
                # Create list of 'None' equal to the length of locations
                normalized_v = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_w):
                logger.info("No W being added to netcdf.")
                # Create list of 'None' equal to the length of locations
                normalized_w = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_settled):
                logger.info("No Settled being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_settled = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_dead):
                logger.info("No Dead being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_dead = [None] * len(normalized_locations) 

            if len(normalized_locations) != len(normalized_halted):
                logger.info("No Halted being added to shapefile.")
                # Create list of 'None' equal to the length of locations
                normalized_halted = [None] * len(normalized_locations) 

            for loc, _temp, _salt, _u, _v, _w, _settled, _dead, _halted in zip(normalized_locations, normalized_temps, normalized_salts, normalized_u, normalized_v, normalized_w, normalized_settled, normalized_dead, normalized_halted):

                if j == 0:
                    time[i] = netCDF4.date2num(loc.time, time_units)
                depth[i, j] = loc.depth
                lat[i, j] = loc.latitude
                lon[i, j] = loc.longitude
                salt[i, j] = _salt
                temp[i, j] = _temp
                u[i, j] = _u
                v[i, j] = _v
                w[i, j] = _w
                settled[i, j] = _settled
                dead[i, j] = _dead
                halted[i, j] = _halted
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

        u.coordinates = "time particle lat lon"
        u.standard_name = "eastward_sea_water_velocity"
        u.units = "m/s"

        v.coordinates = "time particle lat lon"
        v.standard_name = "northward_sea_water_velocity"
        v.units = "m/s"

        w.coordinates = "time particle lat lon"
        w.standard_name = "upward_sea_water_velocity"
        w.units = "m/s"

        settled.coordinates = "time particle lat lon"
        settled.description = "Is the particle settled"
        settled.standard_name = "particle_settled"

        dead.coordinates = "time particle lat lon"
        dead.description = "Is the particle dead"
        dead.standard_name = "particle_dead"

        halted.coordinates = "time particle lat lon"
        halted.description = "Is the particle prevented from being forced by currents"
        halted.standard_name = "particle_halted"

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

        nc.sync()
        nc.close()