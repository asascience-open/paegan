import math
import multiprocessing
from paegan.logging.null_handler import NullHandler
from paegan.utils.asamath import AsaMath
from paegan.utils.asarandom import AsaRandom
from paegan.utils.asatransport import AsaTransport
from paegan.transport.models.base_model import BaseModel

class Transport(BaseModel):
    """
        Transport a particle in the x y and w direction. Requires horizontal and vertical dispersion coefficients.
        Will only move particle when self.move() is called with the proper arguments.
    """

    def __init__(self, **kwargs):

        if "horizDisp" and "vertDisp" in kwargs:
            self._horizDisp = float(kwargs.pop('horizDisp'))
            self._vertDisp = float(kwargs.pop('vertDisp'))
        else:
            raise TypeError( "must provide a horizontal and vertical dispersion coefficient (horizDisp and vertDisp)" )

    def set_horizDisp(self, hdisp):
        self._horizDisp = hdisp
    def get_horizDisp(self):
        return self._horizDisp
    horizDisp = property(get_horizDisp, set_horizDisp)

    def set_vertDisp(self, vdisp):
        self._vertDisp = vdisp
    def get_vertDisp(self):
        return self._vertDisp
    vertDisp = property(get_vertDisp, set_vertDisp)

    def move(self, particle, u, v, w, modelTimestep, **kwargs):
        """
        Returns the lat, lon, H, and velocity of a projected point given a starting
        lat and lon (dec deg), a depth (m) below sea surface (positive up), u, v, and w velocity components (m/s), a horizontal and vertical
        displacement coefficient (m^2/s) H (m), and a model timestep (s).

        GreatCircle calculations are done based on the Vincenty Direct method.

        Returns a dict like:
            {   'latitude': x, 
                'azimuth': x,
                'reverse_azimuth': x, 
                'longitude': x, 
                'depth': x, 
                'u': x
                'v': x, 
                'w': x, 
                'distance': x, 
                'angle': x, 
                'vertical_distance': x, 
                'vertical_angle': x }
        """

        logger = multiprocessing.get_logger()
        logger.addHandler(NullHandler())

        if u is not None and math.isnan(u):
            u = None
        particle.u_vector = u

        if v is not None and math.isnan(v):
            v = None
        particle.v_vector = v

        if w is not None and math.isnan(w):
            w = None
        particle.w_vector = w

        if particle.halted:
            u,v,w = 0,0,0
        else:
            u += AsaRandom.random() * ((2 * self._horizDisp / modelTimestep) ** 0.5) # u transformation calcualtions
            v += AsaRandom.random() * ((2 * self._horizDisp / modelTimestep) ** 0.5) # v transformation calcualtions
            w += AsaRandom.random() * ((2 * self._vertDisp / modelTimestep) ** 0.5) # w transformation calculations

        result = AsaTransport.distance_from_location_using_u_v_w(u=u, v=v, w=w, timestep=modelTimestep, location=particle.location)
        result['u'] = u
        result['v'] = v
        result['w'] = w
        return result

    def __str__(self):
        return  " *** Transport *** " + \
                "\nhorizDisp: " + str(self.horizDisp) + \
                "\nvertDisp: " + str(self.vertDisp)

