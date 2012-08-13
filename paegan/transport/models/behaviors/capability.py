import json
from random import gauss, uniform

class Capability(object):

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

            self.vss = data.get('vss', None)
            self.swim_turning = data.get('swim_turning', None)
            self.non_swim_turning = data.get('nonswim_turning', None)
            self.variance = data.get('variance', None)
            # We initialize the calculated VSS here.  This is not 
            # Recaculated on access.  It needs to be manually recaculated
            # for each Capability.
            self.calculated_vss = self.calculate_vss(method=kwargs.get('method', None))

    def calculate_vss(self, method=None):
        """
        Calculate the vertical swimming speed of this behavior.
        Takes into account the vertical swimming speed and the
        variance.

        Parameters:
            method:  "gaussian" (default) or "random"

            "random" (vss - variance) < X < (vss + variance)
        """
        if self.variance == float(0):
            return self.vss
        else:
            # Calculate gausian distribution and return
            if method == "gaussian" or method is None:
                return gauss(self.vss, self.variance)
            elif method == "random":
                return uniform(self.vss - self.variance, self.vss + self.variance)
            else:
                raise ValueError("Method of vss calculation not recognized, please use 'gaussian' or 'random'")
    def get_calculated_vss(self):
        return self._calculated_vss
    def set_calculated_vss(self, cvss):
        self._calculated_vss = float(cvss)
    calculated_vss = property(get_calculated_vss, set_calculated_vss)

    def get_vss(self):
        return self._vss
    def set_vss(self, vss):
        self._vss = float(vss)
    vss = property(get_vss, set_vss)

    def get_variance(self):
        return self._variance
    def set_variance(self, variance):
        self._variance = float(variance)
    variance = property(get_variance, set_variance)

    def get_nonswim_turning(self):
        return self._non_swim_turning
    def set_nonswim_turning(self, turning):
        self._non_swim_turning = turning
    non_swim_turning = property(get_nonswim_turning, set_nonswim_turning)

    def get_swim_turning(self):
        return self._swim_turning
    def set_swim_turning(self, turning):
        self._swim_turning = turning
    swim_turning = property(get_swim_turning, set_swim_turning)
