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
            except StandardError:
                try:
                    data = kwargs.get('data')
                except StandardError:
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

    def move(self, particle, u, v, w, modelTimestep, **kwargs):

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

        # Grow the particle.  Growth affects which lifestage the particle is in.
        growth = 0.
        do_duration_growth = True
        modelTimestepDays = modelTimestep / 60. / 60. / 24.
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

        # Find the closests Diel that the current particle time is AFTER, and MOVE.
        particle_time = particle.location.time
        active_diel = None
        if len(self.diel) > 0:
            diel_times = [(d.get_time(loc4d=particle.location) - particle_time).total_seconds() for d in self.diel if d.get_time(loc4d=particle.location) > particle_time]
            if len(diel_times) > 0:
                active_diel = self.diel[diel_times.index(min(diel_times))]

        # Run the active diel behavior and all of the taxis behaviors
        # u, v, and w store the continuous resutls from all of the behavior models.
        u = 0
        v = 0
        w = 0

        behaviors_to_run = filter(None, [self.settlement] + [active_diel] + self.taxis)
        # Sort these in the order you want them to be run.

        try:
            vss = self.capability.calculated_vss
        except AttributeError:
            vss = 0

        for behave in behaviors_to_run:
            behave_results = behave.move(particle, 0, 0, vss, modelTimestep, **kwargs)
            u += behave_results['u']
            v += behave_results['v']
            w += behave_results['w']

        # Do the calculation to determine the new location after running the behaviors
        result = AsaTransport.distance_from_location_using_u_v_w(u=u, v=v, w=w, timestep=modelTimestep, location=particle.location)
        result['u'] = u
        result['v'] = v
        result['w'] = w
        return result

class DeadLifeStage(LifeStage):
    def __init__(self, **kwargs):
        super(DeadLifeStage,self).__init__(**kwargs)

    def move(self, particle, u, v, w, modelTimestep, **kwargs):
        """ I'm dead, so no behaviors should act on me """

        # Kill the particle if it isn't settled and isn't already dead.
        if not particle.settled and not particle.dead:
            particle.die()

        # Still save the temperature and salinity for the model output
        temp = kwargs.get('temperature', None)
        if temp is not None and math.isnan(temp):
            temp = None
        particle.temp = temp

        salt = kwargs.get('salinity', None)
        if salt is not None and math.isnan(salt):
            salt = None
        particle.salt = salt

        u = 0
        v = 0
        w = 0

        # Do the calculation to determine the new location
        result = AsaTransport.distance_from_location_using_u_v_w(u=u, v=v, w=w, timestep=modelTimestep, location=particle.location)
        result['u'] = u
        result['v'] = v
        result['w'] = w
        return result