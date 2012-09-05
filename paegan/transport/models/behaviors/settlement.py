import json

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

    def move(self):
        pass