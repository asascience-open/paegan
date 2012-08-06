from shapely.geometry import LineString

class Particle(object):
    """
        A particle
    """
    def __init__(self):
        self._locations = []

    def set_location(self, location):
        self._locations.append(location)
    def get_location(self):
        return self._locations[-1]
    location = property(get_location, set_location)

    def get_locations(self):
        return self._locations
    locations = property(get_locations, None)

    def set_active(self, active):
        self._active = active
    def get_active(self):
        return self._active
    active = property(get_active, set_active)

    def get_last_movement(self):
        return LineString(list(self.locations[-2].point.coords) + list(self.locations[-1].point.coords))

    def linestring(self):
        return LineString(map(lambda x: list(x.point.coords)[0], self.locations))
        
class LarvaParticle(Particle):
    """
        A particle for larvamap, keeps track of information
        for the behaviors component
    """
    def __init__(self):
        self._locations = []
        self.lifestage = 0
        self.lifestage_progress = 0.
        self.temp = []
        self.salt = []
    """    
    def set_temp(self, temp):
        self.temp.append(temp)
    def get_temp(self):
        return self.temp[-1]
    temp = property(get_temp, set_temp)
    
    def get_temps(self):
        return self.temp
    temps = property(get_temps, None)
    
    def set_salt(self, salt):
        self.salt.append(salt)
    def get_salt(self):
        return self.salt[-1]
    salt = property(get_salt, set_salt)
    
    def get_salts(self):
        return self.salt
    salts = property(get_salts, None)
    """
    def update_lifestage_progress(self, **kwargs):
        duration = float(kwargs.pop("lifestage_duration"))
        step = float(kwargs.pop("step"))
        progress = step/duration + self.lifestage_progress
        if progress >= 1:
            self.lifestage += 1
            self.lifestage_progress = 0.
        else:
            self.lifestage_progress = progress
        
class ChemistryParticle(Particle):
    """
        A chemical particle for time and chemistry dependent
        tracers
    """
    def __init__(self):
        pass
        

class OilParticle(Particle):
    """
        An oil particle for special oil physics and chemistry
    """
    def __init__(self):
        pass
