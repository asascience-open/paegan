import json
import multiprocessing
from paegan.logging.null_handler import NullHandler

from paegan.transport.location4d import Location4D

class Settlement(object):

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

            try:
                self.upper = data.get('upper')
                self.lower = data.get('lower')
                self.type = data.get('type')
            except:
                raise ValueError("A settlement must consist of a 'type' and 'upper / 'lower' bounds.")

    def attempt(self, particle, depth):
        logger = multiprocessing.get_logger()
        logger.addHandler(NullHandler())

        # We may want to have settlement affect the u/v/z in the future
        u = 0
        v = 0
        z = 0

        if self.type.lower() == "benthic":
            # Is the sea floor within the upper and lower bounds?
            if self.upper < depth < self.lower:
                # Move the particle to the sea floor.
                # TODO: Should the particle just swim downwards?
                newloc = Location4D(location=particle.location)
                newloc.depth = depth
                particle.location = newloc
                particle.settle()
        elif self.type.lower() == "pelagic":
            # Are we are in enough water to settle
            if self.upper < depth:
                # Is the particle within the range?
                if self.upper < particle.location.depth < self.lower:
                    # Just settle the particle
                    particle.settle()
        else:
            logger.info("Settlement type %s not recognized, not trying to settle Particle %s." % (self.type, str(particle.uid)))

        return (u,v,z)

    def move(self, particle, u, v, z, modelTimestep, **kwargs):

        bathy = kwargs.pop("bathymetry", None)
        if bathy is None:
            return { 'u': 0, 'v': 0, 'z': 0 }

        depth = bathy.get_depth(location=particle.location)
        u,v,z = self.attempt(particle, depth)

        return { 'u': u, 'v': v, 'z': z }
        