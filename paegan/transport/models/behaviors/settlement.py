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

        # If the particle is settled, don't move it anywhere
        if particle.settled:
            return (0,0,0)

        logger.info("Particle trying to settle from: %s" % particle.location)
        logger.info("Bathy at this point is %d" % depth)

        # A particle is negative down from the sea surface, so "-3" is 3 meters below the surface.
        # We are assuming here that the bathymetry is also negative down.

        if self.type.lower() == "benthic":
            # Is the sea floor within the upper and lower bounds?
            if self.upper > depth > self.lower:
                # Move the particle to the sea floor.
                # TODO: Should the particle just swim downwards?
                newloc = Location4D(location=particle.location)
                newloc.depth = depth
                particle.location = newloc
                particle.fill_location_gap()
                particle.settle()
                logger.info("Particle %d settled in %s mode" % (particle.uid, self.type))
        elif self.type.lower() == "pelagic":
            # Are we are in enough water to settle
            if self.upper > depth:
                # Is the particle within the range?
                if self.upper > particle.location.depth > self.lower:
                    # Just settle the particle
                    particle.settle()
                    logger.info("Particle %d settled in %s mode" % (particle.uid, self.type))
        else:
            logger.info("Settlement type %s not recognized, not trying to settle Particle %d." % (self.type, particle.uid))

        return (u,v,z)

    def __str__(self):
        return \
        """*** Settlement  ***
        Upper: %d
        Lower: %d
        Type: %s
        """ % (self.upper, self.lower, self.type)

    def move(self, particle, u, v, z, modelTimestep, **kwargs):

        bathymetry_value = kwargs.pop("bathymetry_value", None)
        if bathymetry_value is None:
            logger.info("No bathymetry so can not attempt to settle particle")
            return { 'u': 0, 'v': 0, 'z': 0 }

        u,v,z = self.attempt(particle, bathymetry_value)

        return { 'u': u, 'v': v, 'z': z }
        