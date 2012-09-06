from paegan.utils.asasuncycles import SunCycles
from paegan.transport.location4d import Location4D
from paegan.utils.asamath import AsaMath
from datetime import datetime, timedelta
import pytz
import json
from paegan.transport.models.base_model import BaseModel

class Diel(BaseModel):

    PATTERN_CYCLE        = "cycles"
    PATTERN_SPECIFICTIME = "specifictime"

    CYCLE_SUNRISE = "sunrise"
    CYCLE_SUNSET  = "sunset"

    HOURS_PLUS  = "+"
    HOURS_MINUS = "-"

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

            self.pattern = data.get('type',None)
            self.cycle = data.get('cycle', None)
            t = data.get('time', None)
            if t is not None:
                # time is in microseconds in JSON
                t = datetime.utcfromtimestamp(t / 1000)
            self.time = t
            self.plus_or_minus = data.get('plus_or_minus', None)
            self.min_depth = data.get('min', None)
            self.max_depth = data.get('max', None)
            self.time_delta = data.get('hours', None)

    def get_pattern(self):
        return self._pattern
    def set_pattern(self, c):
        self._pattern = c
    pattern = property(get_pattern, set_pattern)

    def get_time_delta(self):
        return self._time_delta
    def set_time_delta(self, hours):
        if AsaMath.is_number(hours):
            hours = int(hours)
        self._time_delta = hours
    time_delta = property(get_time_delta, set_time_delta)

    def get_cycle(self):
        return self._cycle
    def set_cycle(self, cycle):
        self._cycle = cycle
    cycle = property(get_cycle, set_cycle)

    def get_min_depth(self):
        return self._min_depth
    def set_min_depth(self, min_depth):
        self._min_depth = float(min_depth)
    min_depth = property(get_min_depth, set_min_depth)

    def get_max_depth(self):
        return self._max_depth
    def set_max_depth(self, max_depth):
        self._max_depth = float(max_depth)
    max_depth = property(get_max_depth, set_max_depth)

    def get_plus_or_minus(self):
        return self._plus_or_minus
    def set_plus_or_minus(self, pom):
        if pom is not None:
            if pom != self.HOURS_PLUS and pom != self.HOURS_MINUS:
                raise ValueError("plus_or_minus must equal '%s' or '%s'" % (self.HOURS_PLUS, self.HOURS_MINUS))
        self._plus_or_minus = pom
    plus_or_minus = property(get_plus_or_minus, set_plus_or_minus)

    def set_time(self, t):
        if t is not None:
            if not isinstance(t, datetime):
                raise ValueError("Time value must be a DateTime")
            t = t.replace(tzinfo=pytz.utc)
        self._time = t
    def get_time(self, loc4d=None):
        """
            Based on a Location4D object and this Diel object, calculate
            the time at which this Diel migration is actually happening
        """
        if self.pattern == self.PATTERN_CYCLE:
            if loc4d is not None:
                c = SunCycles.cycles(loc=loc4d)
                if self.cycle == self.CYCLE_SUNRISE:
                    r = c[SunCycles.RISING]
                elif self.cycle == self.CYCLE_SUNSET:
                    r = c[SunCycles.SETTING]
                td = timedelta(hours=self.time_delta)
                if self.plus_or_minus == self.HOURS_PLUS:
                    r = r + td
                elif self.plus_or_minus == self.HOURS_MINUS:
                    r = r - td
                return r
            else:
                raise ValueError("Location4D object can not be None")

        elif self.pattern == self.PATTERN_SPECIFICTIME:
            return self._time
    time = property(get_time, set_time)

    def move(self, particle, u, v, z, modelTimestep, **kwargs):

        # If the particle is settled, don't move it anywhere
        if particle.settled:
            return { 'u': 0, 'v': 0, 'z': 0 }

        """
            This only works if min is less than max.
            No checks are done here, so it should be done before
            calling this function.
        """

        """ I'm below my desired max depth, so i need to go down

            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            -------------------------------------- min
            -------------------------------------- max
                                x                  me
            ______________________________________
        """
        if particle.location.depth < self.max_depth:
            return { 'u': u, 'v': v, 'z': z }

        """ I'm above my desired max depth, so i need to go down

            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                x                  me
            -------------------------------------- min
            -------------------------------------- max
            ______________________________________
        """
        if particle.location.depth > self.min_depth:
            return { 'u': u, 'v': v, 'z': -z }

        """ I'm in my desired depth, so I'm just gonna chill here

            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            -------------------------------------- min
                                x                  me
            -------------------------------------- max
            ______________________________________
        """
        return { 'u': u, 'v': v, 'z': 0 }

    def __str__(self):
        return \
        """
        Diel:
            Pattern: %s
            Cycle: %s
            Time: %s
            Plus or Minus: %s
            Min Depth: %s
            Max Depth: %s
            Time Delta: %s
        """ % (self.pattern, self.cycle, self._time, self.plus_or_minus, self.min_depth, self.max_depth, self.time_delta)
