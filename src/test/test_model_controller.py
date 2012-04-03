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
    def test_particles(self):
        # Set the start position and time for the models
        start_lat = 38
        start_lon = -76
        start_depth = -5
        num_particles = 3
        time_step = 3600
        num_steps = 50
        temp_time = datetime.utcnow()
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        model = ModelController(latitude=start_lat, longitude=start_lon, depth=start_depth, start=start_time, step=time_step, nstep=num_steps, npart=num_particles, models=[Transport], use_bathymetry=False, use_shoreline=True)
        # Take in a dataset
        model.run()
        print model