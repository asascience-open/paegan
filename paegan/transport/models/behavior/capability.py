import json
from random import gauss

class Capability(object):

    def __init__(self, **kwargs):
        data = {}
        if 'json' in kwargs or 'data' in kwargs:

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

    def calc_vss(self):
        if self.variance == float(0):
            return self.vss
        else:
            # Calculate gausian distribution and return
            return gauss(self.vss, self.variance)

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
