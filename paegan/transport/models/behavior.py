import json
from paegan.transport.models.base_model import BaseModel
from paegan.transport.models.behaviors.lifestage import LifeStage, DeadLifeStage

class LarvaBehavior(BaseModel):

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

        self.lifestages = []
        if data.get('lifestages', None) is not None:
            self.lifestages = [LifeStage(data=ls) for ls in data.get('lifestages')]

        # What do to if the model continues but all LifeStages have passed??
        # Be dead.
        self.lifestages.append(DeadLifeStage())

    def move(self, particle, u, v, w, modelTimestep, **kwargs):

        try:
            lifestage = self.lifestages[particle.lifestage_index]
        except IndexError:
            # The particle should never progress outside of the available lifestages because a Dead
            # particle should not progress and the last lifestage is the DeadLifeStage.
            raise
        
        return lifestage.move(particle, u, v, w, modelTimestep, **kwargs)

    def __str__(self):
        return """
            ***** Behavior *****
              lifestages: %d
            """ % (len(self.lifestages))