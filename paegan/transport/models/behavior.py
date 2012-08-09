import json

class LarvaBehavior(object):

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

        self.lifestages = [LifeStage(ls) for ls in data.get('lifestages')]

    def move(self, **kwargs):

        # Figure out how old the particle is, and which lifestage we should be using
        # Only run that lifestage model