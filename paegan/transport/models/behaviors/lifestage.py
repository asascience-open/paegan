import json
import math
from paegan.transport.models.behaviors.diel import Diel
from paegan.transport.models.behaviors.taxis import Taxis
from paegan.transport.models.behaviors.capability import Capability
from paegan.transport.models.behaviors.settlement import Settlement
from paegan.transport.models.base_model import BaseModel
from paegan.transport.location4d import Location4D
from paegan.utils.asatransport import AsaTransport
import operator
import multiprocessing
from paegan.logging.null_handler import NullHandler

class LifeStage(BaseModel):

    def __init__(self, **kwargs):

        if 'json' in kwargs or 'data' in kwargs:
            data = {}
            try:
                data = json.loads(kwargs['json'])
            except:
                try:
                    data = kwargs.get('data')
                except:
                    pass

            self.name = data.get('name',None)
            self.linear_a = data.get('linear_a', None)
            self.linear_b = data.get('linear_b', None)
            # duration is in days
            self.duration = data.get('duration', None)
            self.diel = [Diel(data=d) for d in data.get('diel')]
            self.taxis = [Taxis(data=t) for t in data.get('taxis')]
            self.capability = None
            if data.get('capability', None) is not None:
                self.capability = Capability(data=data.get('capability'))
            self.settlement = None
            if data.get('settlement', None) is not None:
                self.settlement = Settlement(data=data.get('settlement'))

    def move(self, particle, u, v, z, modelTimestep, **kwargs):

        logger = multiprocessing.get_logger()
        logger.addHandler(NullHandler())

        temp = kwargs.get('temperature', None)
        if temp is not None and math.isnan(temp):
            temp = None
        particle.temp = temp

        salt = kwargs.get('salinity', None)
        if salt is not None and math.isnan(salt):
            salt = None
        particle.salt = salt

        # Find the closests Diel that the current particle time is AFTER, and MOVE.
        particle_time = particle.location.time
        active_diel = None
        if len(self.diel) > 0:
            diel_times = [(d.get_time(loc4d=particle.location) - particle_time).total_seconds() for d in self.diel if d.get_time(loc4d=particle.location) > particle_time]
            if len(diel_times) > 0:
                active_diel = self.diel[diel_times.index(min(diel_times))]

        # Run the active diel behavior and all of the taxis behaviors
        # u, v, and z store the continuous resutls from all of the behavior models.
        u = 0
        v = 0
        z = 0

        behaviors_to_run = filter(None, [self.settlement] + [active_diel] + self.taxis)
        # Sort these in the order you want them to be run.
        for behave in behaviors_to_run:
            behave_results = behave.move(particle, 0, 0, self.capability.calculated_vss, modelTimestep, **kwargs)
            u += behave_results['u']
            v += behave_results['v']
            z += behave_results['z']

        # Grow the particle.  Growth affects which lifestage the particle is in.
        growth = 0.
        do_duration_growth = True
        modelTimestepDays = modelTimestep / 60 / 60 / 24
        if self.linear_a is not None and self.linear_b is not None:
            if particle.temp is not None:
                # linear growth, compute q = t / (Ax+B)
                # Where timestep t (days), at temperature x (deg C), proportion of stage completed (q)
                growth = modelTimestepDays / (self.linear_a * particle.temp + self.linear_b)
                particle.grow(growth)
                do_duration_growth = False
            else:
                logger.info("No temperature found for Particle %s at this location and timestep, skipping linear temperature growth and using duration growth" % particle.uid)
                pass
                
        if do_duration_growth is True:
            growth = modelTimestepDays / self.duration
            particle.grow(growth)

        logger.info("Particle %s grew %f" % (particle.uid, growth))

        # Do the calculation to determine the new location after running the behaviors
        result = AsaTransport.distance_from_location_using_u_v_z(u=u, v=v, z=z, timestep=modelTimestep, location=particle.location)
        result['u'] = u
        result['v'] = v
        result['z'] = z
        return result
