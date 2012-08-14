import unittest
import random
import matplotlib
import matplotlib.pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy
from datetime import datetime, timedelta
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from paegan.transport.model_controller import ModelController
from shapely.geometry import Point
import os

class ModelControllerTest(unittest.TestCase):
    def test_run_individual_particles(self):
        # Set the start position and time for the models
        start_lat = 60.75
        start_lon = -147
        start_depth = 0
        num_particles = 10
        time_step = 3600
        num_steps = 2
        temp_time = datetime.utcnow()
        models = [Transport(horizDisp=0.05, vertDisp=0.0003)]
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        model = ModelController(latitude=start_lat, longitude=start_lon, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True,
            time_chunk=1)
        model.run("http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc", cache=os.path.join(os.path.dirname(__file__), "..", "paegan/transport/_cache"))
        fig = model.generate_map(Point(start_lon, start_lat))
        fig.savefig('test_model_controller.png')
