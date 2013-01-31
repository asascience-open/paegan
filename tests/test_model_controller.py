import os
import shutil
import unittest
import random
import json
import numpy
import urllib
from pytest import raises
from datetime import datetime, timedelta
from paegan.transport.models.transport import Transport
from paegan.transport.models.behavior import LarvaBehavior
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.transport.exceptions import ModelError, DataControllerError
from paegan.utils.asarandom import AsaRandom
from paegan.transport.model_controller import ModelController
from shapely.geometry import Point, Polygon
import os
import pytz
import multiprocessing, logging
from paegan.logging.multi_process_logging import MultiProcessingLogHandler, EasyLogger


class ModelControllerTest(unittest.TestCase):

    def setUp(self):
        self.start_lat = 60.75
        self.start_lon = -147
        self.start_depth = 0
        self.num_particles = 4
        self.time_step = 3600
        self.num_steps = 10
        self.start_time = datetime(2012, 8, 1, 00)
        self.transport = Transport(horizDisp=0.05, vertDisp=0.0003)

        self.log = EasyLogger('testlog.txt', logging.INFO)

    def tearDown(self):
        self.log.close()

    def test_run_from_point(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_run_from_point")

        models = [self.transport]

        p = Point(self.start_lon, self.start_lat, self.start_depth)

        model = ModelController(geometry=p, start=self.start_time, step=self.time_step, nstep=self.num_steps, npart=self.num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=10, horiz_chunk=4)

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_run_from_point.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path)

    def test_run_from_polygon(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_run_from_polygon")

        models = [self.transport]

        poly = Point(self.start_lon, self.start_lat, self.start_depth).buffer(0.001)

        model = ModelController(geometry=poly, start=self.start_time, step=self.time_step, nstep=self.num_steps, npart=self.num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=10, horiz_chunk=4)

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_run_from_polygon.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path)

    def test_interp(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_interp")

        models = [self.transport]

        model = ModelController(latitude=self.start_lat, longitude=self.start_lon, depth=self.start_depth, start=self.start_time, step=self.time_step, nstep=self.num_steps, npart=self.num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=10, horiz_chunk=4)

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_interp.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path)

    def test_nearest(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_nearest")

        models = [self.transport]
        
        model = ModelController(latitude=self.start_lat, longitude=self.start_lon, depth=self.start_depth, start=self.start_time, step=self.time_step, nstep=self.num_steps, npart=self.num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=10, horiz_chunk=4, time_method='nearest')

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_nearest.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path)

    def test_start_on_land(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_start_on_land")

        # Set the start position and time for the models
        start_lat = 60.15551950079041
        start_lon = -148.1999130249019

        models = [self.transport]

        model = ModelController(latitude=start_lat, longitude=start_lon, depth=self.start_depth, start=self.start_time, step=self.time_step, nstep=self.num_steps, npart=self.num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=10, horiz_chunk=4, time_method='nearest')

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_start_on_land.nc")

        with raises(ModelError):
            model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=cache_path)

    def test_bad_dataset(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_bad_dataset")

        models = [self.transport]

        model = ModelController(latitude=self.start_lat, longitude=self.start_lon, depth=self.start_depth, start=self.start_time, step=self.time_step, nstep=self.num_steps, npart=self.num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=10, horiz_chunk=4, time_method='nearest')

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_bad_dataset.nc")
        
        with raises(DataControllerError):
            model.run("http://asascience.com/thisisnotadataset.nc", cache=cache_path)

    """
    def test_behavior_growth_and_settlement(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_behavior_growth_and_settlement")

        # 6 days
        num_steps = 144

        num_particles = 2

        # Behavior
        behavior_config = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/behavior_for_run_testing.json"))).read()
        lb = LarvaBehavior(json=behavior_config)

        models = [self.transport]
        models.append(lb)

        model = ModelController(latitude=self.start_lat, longitude=self.start_lon, depth=self.start_depth, start=self.start_time, step=self.time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=True, use_shoreline=True,
            time_chunk=24, horiz_chunk=4, time_method='nearest')

        output_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_output/behaviors")
        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)
        output_formats = ['Shapefile','NetCDF','Trackline']

        bathy_path = os.path.normpath(os.path.join(__file__,"../../paegan/resources/bathymetry/ETOPO1_Bed_g_gmt4.grd"))

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_behavior_growth_and_settlement.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", bathy=bathy_path, cache=cache_path, output_path=output_path, output_formats=output_formats)
    """

    def test_quick_settlement(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_quick_settlement")

        num_steps = 24

        num_particles = 4

        # Behavior
        behavior_config = open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/behavior_quick_settle.json"))).read()
        lb = LarvaBehavior(json=behavior_config)

        models = [self.transport]
        models.append(lb)

        model = ModelController(latitude=self.start_lat, longitude=self.start_lon, depth=self.start_depth, start=self.start_time, step=self.time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=True, use_shoreline=True,
            time_chunk=12, horiz_chunk=2, time_method='nearest')

        output_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_output/behaviors")
        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)
        output_formats = ['Shapefile','NetCDF','Trackline','Pickle']

        bathy_path = os.path.normpath(os.path.join(__file__,"../../paegan/resources/bathymetry/ETOPO1_Bed_g_gmt4.grd"))

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_quick_settlement.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", bathy=bathy_path, cache=cache_path, output_path=output_path, output_formats=output_formats)

    def test_timechunk_greater_than_timestep(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: test_timechunk_greater_than_timestep")

        # 6 days
        num_steps = 10

        num_particles = 2

        models = [self.transport]

        model = ModelController(latitude=self.start_lat, longitude=self.start_lon, depth=self.start_depth, start=self.start_time, step=self.time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=True, use_shoreline=True,
            time_chunk=24, horiz_chunk=2)

        bathy_path = os.path.normpath(os.path.join(__file__,"../../paegan/resources/bathymetry/ETOPO1_Bed_g_gmt4.grd"))

        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/test_timechunk_greater_than_timestep.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", bathy=bathy_path, cache=cache_path)

    
    def test_kayak_island(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: Kayak Island")

        # 6 days
        num_steps = 1632

        num_particles = 100

        time_step = 3600

        behavior_config = json.loads(urllib.urlopen("http://behaviors.larvamap.asascience.com/library/50ef1bb1cc7b61000700001d.json").read())
        lb = LarvaBehavior(data=behavior_config[u'results'][0])

        #behavior_config = json.loads(open(os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/nick.json"))).read())
        #lb = LarvaBehavior(data=behavior_config[u'results'][0])

        models = [Transport(horizDisp=0.01, vertDisp=0.001)]
        models.append(lb)

        start_time = datetime(2011, 5, 2, 00, tzinfo=pytz.utc)

        start_lat = 59.93517413488866
        start_lon = -144.496213677788
        depth = -1

        shoreline_path = os.path.normpath(os.path.join(__file__,"../../paegan/resources/shoreline/westcoast/New_Land_Clean.shp"))

        model = ModelController(latitude=start_lat, longitude=start_lon, depth=depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=True, use_shoreline=True,
            time_chunk=24, horiz_chunk=5, time_method='interp', shoreline_path=shoreline_path)

        output_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_output/kayak_island")
        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)
        output_formats = ['Shapefile','NetCDF','Trackline']

        bathy_path = os.path.normpath(os.path.join(__file__,"../../paegan/resources/bathymetry/ETOPO1_Bed_g_gmt4.grd"))
        
        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/kayak_island.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L1_FCST.nc", bathy=bathy_path, cache=cache_path, output_path=output_path, output_formats=output_formats)
        
    def test_sheep_bay(self):
        self.log.logger.info("**************************************")
        self.log.logger.info("Running: Sheep Bay")

        # 6 days
        num_steps = 1632

        num_particles = 100

        time_step = 3600

        behavior_config = json.loads(urllib.urlopen("http://behaviors.larvamap.asascience.com/library/50ef1bb1cc7b61000700001d.json").read())
        lb = LarvaBehavior(data=behavior_config[u'results'][0])

        models = [Transport(horizDisp=0.01, vertDisp=0.001)]
        models.append(lb)

        start_time = datetime(2011, 5, 2, 00, tzinfo=pytz.utc)

        start_lat = 60.60899655733162
        start_lon = -145.97402533055956
        depth = -1

        shoreline_path = os.path.normpath(os.path.join(__file__,"../../paegan/resources/shoreline/alaska/AK_Land_Basemap.shp"))

        model = ModelController(latitude=start_lat, longitude=start_lon, depth=depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=True, use_shoreline=True,
            time_chunk=24, horiz_chunk=5, time_method='interp', shoreline_path=shoreline_path)

        output_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_output/sheep_bay")
        shutil.rmtree(output_path, ignore_errors=True)
        os.makedirs(output_path)
        output_formats = ['Shapefile','NetCDF','Trackline']

        bathy_path = os.path.normpath(os.path.join(__file__,"../../paegan/resources/bathymetry/ETOPO1_Bed_g_gmt4.grd"))
        
        cache_path = os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache/sheep_bay.nc")
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", bathy=bathy_path, cache=cache_path, output_path=output_path, output_formats=output_formats)
    