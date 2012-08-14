import json
from paegan.transport.models.base_model import BaseModel
from paegan.transport.models.behaviors.lifestage import LifeStage

class LarvaBehavior(BaseModel):

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

        self.lifestages = []
        if data.get('lifestages', None) is not None:
            self.lifestages = [LifeStage(data=ls) for ls in data.get('lifestages')]

    def move(self, particle, u, v, z, modelTimestep, **kwargs):
        # Only run that lifestage model that corresponds to the particles growth progress
        return self.lifestages[particle.lifestage_index].move(particle, u, v, z, modelTimestep, **kwargs)