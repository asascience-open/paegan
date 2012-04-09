import unittest
import random
import matplotlib
import matplotlib.pyplot
from mpl_toolkits.mplot3d import Axes3D
import numpy
from datetime import datetime, timedelta
from src.transport.models.transport import Transport
from src.transport.particles.particle import Particle
from src.transport.location4d import Location4D
from src.utils.asarandom import AsaRandom
from src.transport.model_controller import ModelController

class ModelControllerTest(unittest.TestCase):
    def test_run_individual_particles(self):
        # Set the start position and time for the models
        start_lat = 39
        start_lon = -70
        start_depth = 0
        num_particles = 5
        time_step = 3600
        num_steps = 1000
        temp_time = datetime.utcnow()
        models = [Transport]
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        model = ModelController(latitude=start_lat, longitude=start_lon, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True)
        model.run()
        model.generate_map()

    def test_run_individual_timesteps(self):
        # Set the start position and time for the models
        start_lat = 39
        start_lon = -70
        start_depth = -50
        num_particles = 5
        time_step = 3600
        num_steps = 1000
        temp_time = datetime.utcnow()
        models = [Transport]
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        model = ModelController(latitude=start_lat, longitude=start_lon, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=models, use_bathymetry=False, use_shoreline=True)
        model.run_by_time()
        model.generate_map()
