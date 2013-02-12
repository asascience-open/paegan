from shapely.geometry import LineString

class Particle(object):
    """
        A particle
    """
    def __init__(self, **kwargs):
        self._id = kwargs.get("id", -1)
        self._locations = []

        self._age = 0. # Age in days
        self._ages = [0.] # Age in days   

        self._u = None
        self._us = []

        self._v = None
        self._vs = []

        self._w = None
        self._ws = []

        self._halted = False
        self._halts = []

        self._note = ""
        self._notes = []

    def get_id(self):
        return self._id
    uid = property(get_id)

    def set_location(self, location):
        self._locations.append(location)
    def get_location(self):
        return self._locations[-1]
    location = property(get_location, set_location)
    def get_locations(self):
        return self._locations
    locations = property(get_locations, None)

    def save(self):
        self.halts.append(self.halted)
        self.u_vectors.append(self.u_vector)
        self.v_vectors.append(self.v_vector)
        self.w_vectors.append(self.w_vector)
        self.notes.append(self.note)
        self.ages.append(self.get_age(units='days'))

        self.u_vector = None
        self.v_vector = None
        self.w_vector = None
        self.note = ""

    def fill_status_gap(self, value=None):

        def fillvalue(v):
            if unicode(value).lower() == u"last":
                return v
            else:
                return value

        if len(self.locations) > len(self.halts):
            self.halts.append(self.halted)

        if len(self.locations) > len(self.ages):
            self.ages.append(self.get_age(units='days'))

    def fill_environment_gap(self, value=None):

        def fillvalue(v):
            if unicode(value).lower() == u"last":
                return v
            else:
                return value

        if len(self.locations) > len(self.u_vectors):
            self.u_vectors.append(fillvalue(self.last_u()))

        if len(self.locations) > len(self.v_vectors):
            self.v_vectors.append(fillvalue(self.last_v()))

        if len(self.locations) > len(self.w_vectors):
            self.w_vectors.append(fillvalue(self.last_w()))

    def fill_gap(self, value=None):
        self.fill_environment_gap(value=value)
        self.fill_status_gap(value=value)

    def set_u_vector(self, u):
        self._u = u
    def get_u_vector(self):
        return self._u
    u_vector = property(get_u_vector, set_u_vector)
    def get_u_vectors(self):
        return self._us
    u_vectors = property(get_u_vectors, None)
    def last_u(self):
        try:
            return self.u_vectors[-1]
        except IndexError:
            return None
    
    def set_v_vector(self, v):
        self._v = v
    def get_v_vector(self):
        return self._v
    v_vector = property(get_v_vector, set_v_vector)
    def get_v_vectors(self):
        return self._vs
    v_vectors = property(get_v_vectors, None)
    def last_v(self):
        try:
            return self.v_vectors[-1]
        except IndexError:
            return None

    def set_w_vector(self, w):
        self._w = w
    def get_w_vector(self):
        return self._w
    w_vector = property(get_w_vector, set_w_vector)
    def get_w_vectors(self):
        return self._ws
    w_vectors = property(get_w_vectors, None)
    def last_w(self):
        try:
            return self.w_vectors[-1]
        except IndexError:
            return None    

    def get_ages(self):
        return self._ages
    ages = property(get_ages, None)

    def set_note(self, note):
        self._note = note
    def get_note(self):
        return self._note
    note = property(get_note, set_note)
    def get_notes(self):
        return self._notes
    notes = property(get_notes, None)
    def last_note(self):
        try:
            return self.notes[-1]
        except IndexError:
            return ""  

    def proceed(self):
        """
        Unhalt the movement of this particle.
        """
        self._halted = False
    def halt(self):
        """
        Halt the movement of this particle.
        """
        self._halted = True
    def get_halted(self):
        return self._halted
    halted = property(get_halted, None)
    def get_halts(self):
        return self._halts
    halts = property(get_halts, None)

    def set_active(self, active):
        self._active = active
    def get_active(self):
        return self._active
    active = property(get_active, set_active)

    def get_last_movement(self):
        return LineString(list(self.locations[-2].point.coords) + list(self.locations[-1].point.coords))

    def get_age(self, **kwargs):
        """
        Returns the particlees age (how long it has been forced) in a variety of units.
        Rounded to 8 decimal places.

        Parameters:
            units (optional) = 'days' (default), 'hours', 'minutes', or 'seconds'
        """
        try:
            units = kwargs.get('units', None)
            if units is None:
                return self._age
            units = units.lower()
            if units == "days":
                z = self._age
            elif units == "hours":
                z = self._age * 24.
            elif units == "minutes":
                z = self._age * 24. * 60.
            elif units == "seconds":
                z = self._age * 24. * 60. * 60.
            else:
                raise
            return round(z,8) 
        except StandardError:
            raise KeyError("Could not return age of particle")

    def age(self, **kwargs):
        """
        Age this particle.

        parameters (optional, only one allowed):
            days (default)
            hours
            minutes
            seconds
        """
        if kwargs.get('days', None) is not None:
            self._age += kwargs.get('days')
            return
        if kwargs.get('hours', None) is not None:
            self._age += kwargs.get('hours') / 24.
            return
        if kwargs.get('minutes', None) is not None:
            self._age += kwargs.get('minutes') / 24. / 60.
            return
        if kwargs.get('seconds', None) is not None:
            self._age += kwargs.get('seconds') / 24. / 60. / 60.
            return

        raise KeyError("Could not age particle, please specify 'days', 'hours', 'minutes', or 'seconds' parameter")

    def linestring(self):
        return LineString(map(lambda x: list(x.point.coords)[0], self.locations))

    def normalized_locations(self, model_timesteps):
        inds = self.normalized_indexes(model_timesteps)
        return [loc for i,loc in enumerate(self.locations) if i in inds]

    def normalized_indexes(self, model_timesteps):
        """
        This function will normalize the particles locations
        to the timestep of the model that was run.  This is used
        in output, as we should only be outputting the model timestep
        that was chosen to be run.

        In most cases, the length of the model_timesteps and the 
        particle's locations will be the same (unless it hits shore).

        If they are not the same length pull out of locations the timesteps
        that are closest to the model_timesteps
        """

        # Clean up locations
        # If duplicate time instances, remove the lower index 
        clean_locs = []
        for i,loc in enumerate(self.locations):
            try:
                if loc.time == self.locations[i+1].time:
                    continue
                else:
                    clean_locs.append(loc)
            except StandardError:
                clean_locs.append(loc)

        if len(clean_locs) == len(model_timesteps):
           return [ind for ind,loc in enumerate(self.locations) if loc in clean_locs]
        elif len(model_timesteps) < len(clean_locs):
            # We have at least one internal timestep for this particle
            # Pull out the matching location indexes
            indexes = [ind for ind,loc in enumerate(self.locations) if loc in clean_locs]
            if len(model_timesteps) == len(indexes):
                return indexes
            raise ValueError("Can't normalize")           
        elif len(model_timesteps) > len(clean_locs):
            # The particle stopped before forcing for all of the model timesteps
            raise ValueError("Particle has less locations than model timesteps")

        
class LarvaParticle(Particle):
    """
        A particle for larvamap, keeps track of information
        for the behaviors component
    """
    def __init__(self, **kwargs):
        super(LarvaParticle,self).__init__(**kwargs)
        self.lifestage_progress = 0.

        self._temp = None
        self._temps = []

        self._salt = None
        self._salts = []

        self._settled = False
        self._settles = []

        self._dead = False
        self._deads = []

    # Temp
    def set_temp(self, temp):
        self._temp = temp
    def get_temp(self):
        return self._temp
    temp = property(get_temp, set_temp)
    def get_temps(self):
        return self._temps
    temps = property(get_temps, None)
    def last_temp(self):
        try:
            return self.temps[-1]
        except IndexError:
            return None
    
    # Salt
    def set_salt(self, salt):
        self._salt = salt
    def get_salt(self):
        return self._salt
    salt = property(get_salt, set_salt)
    def get_salts(self):
        return self._salts
    salts = property(get_salts, None)
    def last_salt(self):
        try:
            return self.salts[-1]
        except IndexError:
            return None
    
    def get_lifestage_index(self):
        return int(self.lifestage_progress)
    lifestage_index = property(get_lifestage_index, None)

    def settle(self):
        self._settled = True
        self.halt()
    def unsettle(self):
        self._settled = False
        self.proceed()
    def get_settled(self):
        return self._settled
    settled = property(get_settled, None)
    def get_settles(self):
        return self._settles
    settles = property(get_settles, None)

    def die(self):
        self._dead = True
        self._deads
    def undie(self):
        self._dead = False
    def get_dead(self):
        return self._dead
    dead = property(get_dead, None)
    def get_deads(self):
        return self._deads
    deads = property(get_deads, None)

    def save(self):
        super(LarvaParticle,self).save()
        self.deads.append(self.dead)
        self.settles.append(self.settled)
        self.temps.append(self.temp)
        self.salts.append(self.salt)

        self.temp = None
        self.salt = None

    def fill_status_gap(self, value=None):
        super(LarvaParticle,self).fill_status_gap(value=value)

        def fillvalue(v):
            if unicode(value).lower() == u"last":
                return v
            else:
                return value

        if len(self.locations) > len(self.deads):
            self.deads.append(self.dead)

        if len(self.locations) > len(self.settles):
            self.settles.append(self.settled)

    def fill_environment_gap(self, value=None):
        super(LarvaParticle,self).fill_environment_gap(value=value)

        def fillvalue(v):
            if unicode(value).lower() == u"last":
                return v
            else:
                return value

        if len(self.locations) > len(self.salts):
            self.salts.append(fillvalue(self.last_salt()))

        if len(self.locations) > len(self.temps):
            self.temps.append(fillvalue(self.last_temp()))

    def fill_gap(self, value=None):
        super(LarvaParticle,self).fill_gap(value=value)

    def grow(self, amount):
        """
        Grow a particle by a percentage value (0 < x < 1)

        When a particle grows past 1, its current lifestage is 
        complete and it moves onto the next.

        The calculation to get the current lifestage index is in get_lifestage_index()
        """
        self.lifestage_progress += amount
        
    def logstring(self):
        return "Particle %d (Age: %.3f days, Lifestage %d: %.3f%%, Status: %s)" % (self.uid, self.get_age(units='days'), self.lifestage_index, (self.lifestage_progress % 1) * 100., self.status())

    def outputstring(self):
        """ For shapefiles, max 254 characters """
        return "Age: %.3f days\nLifestage %d: %.3f%%\n" % (self.get_age(units='days'), self.lifestage_index, (self.lifestage_progress % 1) * 100.)

    def status(self):
        return "settled - %s / dead - %s / halted - %s" % (self.settled, self.dead, self.halted)

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
