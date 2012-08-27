import os
import shutil
import unittest
import random
import matplotlib
import matplotlib.pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy
from datetime import datetime, timedelta
from paegan.transport.models.transport import Transport
from paegan.transport.models.behavior import LarvaBehavior
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from paegan.transport.model_controller import ModelController
from shapely.geometry import Point, Polygon
import os
import multiprocessing, logging
from paegan.logging.multi_process_logging import MultiProcessingLogHandler, EasyLogger


class ModelControllerTest(unittest.TestCase):
    def test_run_individual_particles(self):
        print "lat / lon"
        # Set the start position and time for the models
        start_lat = 60.75
        start_lon = -147
        start_depth = 0
        num_particles = 10
        time_step = 3600
        num_steps = 2
        models = [Transport(horizDisp=0.05, vertDisp=0.0003)]
        start_time = datetime(2012, 8, 1, 00)

        model = ModelController(latitude=start_lat, longitude=start_lon, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=2, horiz_chunk=2)

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache")
        output_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_output/transport")
        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)
        output_formats = ['Shapefile','NetCDF','Trackline']

        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path, output_path=output_path, output_formats=output_formats)

    def test_run_from_point(self):
        print "point"
        # Set the start position and time for the models
        start_lat = 60.75
        start_lon = -147
        start_depth = 0
        num_particles = 2
        time_step = 3600
        num_steps = 2
        models = [Transport(horizDisp=0.05, vertDisp=0.0003)]
        start_time = datetime(2012, 8, 1, 00)

        p = Point(start_lon, start_lat, start_depth)

        model = ModelController(geometry=p, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=2, horiz_chunk=2)

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path)

    def test_run_from_polygon(self):
        # Set the start position and time for the models
        print "polygon"
        start_lat = 60.75
        start_lon = -147
        start_depth = 10
        num_particles = 2
        time_step = 3600
        num_steps = 2
        models = [Transport(horizDisp=0.05, vertDisp=0.0003)]
        start_time = datetime(2012, 8, 1, 00)

        poly = Point(start_lon, start_lat, start_depth).buffer(0.001)

        model = ModelController(geometry=poly, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=2, horiz_chunk=2)

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path)

    def test_run_behaviors(self):
        # Set the start position and time for the models
        print "behavior"
        start_lat = 60.75
        start_lon = -147
        start_depth = 0
        num_particles = 4
        time_step = 3600
        num_steps = 10

        models = []
        models.append(Transport(horizDisp=0.05, vertDisp=0.0003))

        behavior_config = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/behavior_for_run_testing.json"))).read()
        lb = LarvaBehavior(json=behavior_config)
        
        models.append(lb)

        start_time = datetime(2012, 8, 1, 00)

        log = EasyLogger('testlog.txt')
        log.logger.info('From Test')

        model = ModelController(latitude=start_lat, longitude=start_lon, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=10, horiz_chunk=2)

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache")
        output_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_output/behaviors")
        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)
        output_formats = ['Shapefile','NetCDF','Trackline']

        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path, output_path=output_path, output_formats=output_formats)

        log.close()