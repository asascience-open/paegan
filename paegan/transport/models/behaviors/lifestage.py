import json
from paegan.transport.models.behaviors.diel import Diel
from paegan.transport.models.behaviors.taxis import Taxis
from paegan.transport.models.behaviors.capability import Capability

class LifeStage(object):

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

    def move(self, particle, u, v, z, modelTimestep, **kwargs):

        particle.temp = kwargs.get('temperature')
        particle.salt = kwargs.get('salinity')

        # Run the nested behaviors
        for d in self.diel:
            d.move(particle, u, v, z, modelTimestep, **kwargs)

        for t in self.taxis:
            t.move(particle, u, v, z, modelTimestep, **kwargs)

        # Grow the particle.  Growth effects which lifestage the particle is in.
        do_duration_growth = True
        modelTimestepDays = modelTimestep / 60 / 60 / 24
        if self.linear_a is not None and self.linear_b is not None:
            if particle.temp is not None:
                # linear growth, compute q = t / (Ax+B)
                # Where timestep t (days), at temperature x (deg C), proportion of stage completed (q)
                q = modelTimestepDays / (linear_a * particle.temp + linear_b)
                particle.grow(q)
                do_duration_growth = False
            else:
                print "No temperature found for particle at this location and timestep, skipping linear temperature growth and using duration growth"
                
        if self.do_duration_growth is True:
            particle.grow(modelTimestepDays / self.duration)