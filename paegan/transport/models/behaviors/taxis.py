import json
from paegan.transport.models.base_model import BaseModel

class Taxis(BaseModel):

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

            # Convert from positive down to negative down
            self.min_value = data.get('min') * -1.
            self.max_value = data.get('max') * -1.
            self.gradient = data.get('gradient',None)
            self.variable = data.get('variable',None)
            self.units = data.get('units',None)

    def get_min_value(self):
        return self._min_value
    def set_min_value(self, min_value):
        self._min_value = float(min_value)
    min_value = property(get_min_value, set_min_value)

    def get_max_value(self):
        return self._max_value
    def set_max_value(self, max_value):
        self._max_value = float(max_value)
    max_value = property(get_max_value, set_max_value)

    def get_gradient(self):
        return self._gradient
    def set_gradient(self, gradient):
        self._gradient = float(gradient)
    gradient = property(get_gradient, set_gradient)

    def get_variable(self):
        return self._variable
    def set_variable(self, variable):
        self._variable = variable
    variable = property(get_variable, set_variable)

    def get_units(self):
        return self._units
    def set_units(self, units):
        self._units = unicode(units)
    units = property(get_units, set_units)

    def __str__(self):
        return \
        """
          Min: %d
          Max: %d
          Gradient: %d
          Variables: %s
          Units: %s
        """ % (self.min_value, self.max_value, self.gradient, self.variable, self.units)

    def move(self, particle, u, v, w, modelTimestep, **kwargs):

        # If the particle is settled, don't move it anywhere
        if particle.settled:
            return { 'u': 0, 'v': 0, 'w': 0 }

        # If the particle is halted (but not settled), don't move it anywhere
        if particle.halted:
            return { 'u': 0, 'v': 0, 'w': 0 }
        
        u = 0
        v = 0
        w = 0
        return { 'u': u, 'v': v, 'w': w }