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

class TransportTest(unittest.TestCase):
    def test_single_particle(self):
        p = Particle() # create a particle instance 'p'
        # Set the start position of the Particle
        start_lat = 38
        start_lon = -76
        start_depth = -5
        temp_time = datetime.utcnow()
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)

        loc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=start_time)
        p.location = loc # set particle location
        
        times = [0, 3600, 7200, 10800] # in seconds
        horizDisp=0.05 # in meters^2 / second
        vertDisp=0.00003 # in meters^2 / second
        u = [0.3, 0.2, 0.1, 0.05] # in m/s
        v = [-0.1, -0.3, -0.06, -0.2] # in m/s
        z = [0.005, 0.002, 0.001, -0.003] # in m/s

        for i in xrange(0, len(times)):
            #print p.get_current_location()
            transport_model = Transport() # create a transport instance
            current_location = p.location
            try:
                modelTimestep = times[i+1] - times[i]
                calculatedTime = times[i+1]
            except:
                modelTimestep = times[i] - times[i-1]
                calculatedTime = times[i] + modelTimestep
            movement = transport_model.move(current_location.latitude, current_location.longitude, current_location.depth, u[i], v[i], z[i], horizDisp, vertDisp, modelTimestep)
            newloc = Location4D(latitude=movement['lat'], longitude=movement['lon'], depth=movement['depth'])
            newloc.u = movement['u']
            newloc.v = movement['v']
            newloc.z = movement['z']
            newloc.time = start_time + timedelta(seconds=calculatedTime)
            p.location = newloc
            
        #print p.linestring()
        #for u in xrange(0,len(p.get_locations())):
        #    print p.get_locations()[u]

    def test_multiple_particles(self):
        # Constants
        horizDisp=0.05 # in meters^2 / second
        vertDisp=0.00003 # in meters^2 / second
        times = range(0,360001,3600) # in seconds
        start_lat = 38
        start_lon = -76
        start_depth = -5
        temp_time = datetime.utcnow()
        start_time = datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour)
        # empty array for storing particle objects
        arr = []
        # Generate u,v,z as random numbers
        u=[]
        v=[]
        z=[]
        for w in xrange(0,100):
            z.append(random.gauss(0,0.0001)) # gaussian in m/s
            u.append(abs(AsaRandom.random())) # random function in m/s
            v.append(abs(AsaRandom.random())) # random function in m/s

        for i in xrange(0,3):
            p = Particle()

            loc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=start_time)
            p.location = loc # set particle location

            for i in xrange(0, len(times)-1):
                #print t
                #print p.get_current_location()
                transport_model = Transport() # create a transport instance
                current_location = p.location
                try:
                    modelTimestep = times[i+1] - times[i]
                    calculatedTime = times[i+1]
                except:
                    modelTimestep = times[i] - times[i-1]
                    calculatedTime = times[i] + modelTimestep
                movement = transport_model.move(current_location.latitude, current_location.longitude, current_location.depth, u[i], v[i], z[i], horizDisp, vertDisp, modelTimestep)
                newloc = Location4D(latitude=movement['lat'], longitude=movement['lon'], depth=movement['depth'])
                newloc.u = movement['u']
                newloc.v = movement['v']
                newloc.z = movement['z']
                newloc.time = start_time + timedelta(seconds=calculatedTime)
                p.location = newloc
            arr.append(p)
        
        # 3D plot
        fig = matplotlib.pyplot.figure() # call a blank figure
        ax = fig.gca(projection='3d') # line with points
        # ax = fig.add_subplot(111, projection='3d') # scatter

        # 2D plot
        #fig = matplotlib.pyplot.figure() # call blank figure
        #ax = fig.add_subplot(111) # scatter plot

        #for x in range(len(arr)):
        for x in range(3):
            particle=arr[x]
            p_proj_lats=[]
            p_proj_lons=[]
            p_proj_depths=[]

            for y in range(len(particle.locations)):
                p_proj_lats.append(particle.locations[y].get_latitude())
                p_proj_lons.append(particle.locations[y].get_longitude())
                p_proj_depths.append(particle.locations[y].get_depth())
            ax.plot(p_proj_lons, p_proj_lats, p_proj_depths, marker='o') # 3D line plot with point

            # ax.scatter(p_proj_lons, p_proj_lats, p_proj_depths, c='r', marker='o') # 3D scatter plot just points
            #col=['r','b','g']
            #ax.scatter(p_proj_lons, p_proj_lats, marker='o', c=col) # 2D scatter plot just points

        #print p_proj_depths
        #print p_proj_lons
        #print p_proj_lats
        #ax2.scatter(p_proj_lons, p_proj_lats, p_proj_depths, c='r', marker='o', linestyle='solid')
        #ax.scatter(p_proj_lons, p_proj_lats, p_proj_depths, c='r', marker='o')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_zlabel('Depth (m)')
        matplotlib.pyplot.show()
       
