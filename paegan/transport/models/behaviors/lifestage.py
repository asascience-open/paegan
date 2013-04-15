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
from datetime import timedelta

from paegan.logger import logger

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

    def get_active_diel(self, loc4d):
        active_diel = None
        if len(self.diel) > 0:
            particle_time = loc4d.time
            # Find the closests Diel that the current particle time is AFTER, and set it to the active_diel
            closest = None
            closest_seconds = None
            for ad in self.diel:
                # To handle thecase where a particle at 1:00am only looks at Diels for that
                # day and does not act upon Diel from the previous day at, say 11pm, check
                # both today's Diel times and the particles current days Diel times.
                yesterday = Location4D(location=loc4d)
                yesterday.time = yesterday.time - timedelta(days=1)

                times = [ad.get_time(loc4d=loc4d), ad.get_time(loc4d=yesterday)]
                for t in times:
                    if t <= particle_time:
                        seconds = (particle_time - t).total_seconds()
                        if closest is None or seconds < closest_seconds:
                            closest = ad
                            closest_seconds = seconds

                del yesterday

            active_diel = closest

        return active_diel

    def move(self, particle, u, v, w, modelTimestep, **kwargs):

        temp = kwargs.get('temperature', None)
        salt = kwargs.get('salinity', None)
        
        logger.debug("Temp: %.4f, Salt: %.4f" %(temp,salt))

        # IMPORTANT:
        # If we got no data from the model, we are using the last available value stored in the particles!
        if (temp is None) or (temp is not None and math.isnan(temp)):
            temp = particle.last_temp()
        if (salt is None) or (salt is not None and math.isnan(salt)):
            salt = particle.last_salt()

        particle.temp = temp
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
                logger.debug("No temperature found for Particle %s at this location and timestep, skipping linear temperature growth and using duration growth" % particle.uid)
                pass
                
        if do_duration_growth is True:
            growth = modelTimestepDays / self.duration
            particle.grow(growth)

        active_diel = self.get_active_diel(particle.location)

        # Run the active diel behavior and all of the taxis behaviors
        # u, v, and w store the continuous results from all of the behavior models.
        u = 0
        v = 0
        w = 0

        behaviors_to_run = filter(None, [self.settlement] + [active_diel] + self.taxis)
        # Sort these in the order you want them to be run.

        try:
            vss = self.capability.calculated_vss
        except AttributeError:
            logger.debug("No VSS found, vertical behaviors will not act upon particle")
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