from paegan.utils.asasuncycles import SunCycles
from paegan.transport.location4d import Location4D
from paegan.utils.asamath import AsaMath
from datetime import datetime, timedelta
import pytz
import json
from paegan.transport.models.base_model import BaseModel

from paegan.logger import logger

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
            except StandardError:
                try:
                    data = kwargs.get('data')
                except StandardError:
                    pass

            self.pattern = data.get('type',None)
            self.cycle = data.get('cycle', None)
            t = data.get('time', None)
            if t is not None:
                # time is in microseconds in JSON
                t = datetime.utcfromtimestamp(t / 1000)
            self.time = t
            self.plus_or_minus = data.get('plus_or_minus', None)
            # Convert from positive down to negative down
            self.min_depth = data.get('min') * -1.
            self.max_depth = data.get('max') * -1.
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
        if loc4d is None:
            raise ValueError("Location4D object can not be None")

        if self.pattern == self.PATTERN_CYCLE:
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
        elif self.pattern == self.PATTERN_SPECIFICTIME:
            return self._time.replace(year=loc4d.time.year, month=loc4d.time.month, day=loc4d.time.day)
    time = property(get_time, set_time)

    def move(self, particle, u, v, w, modelTimestep, **kwargs):

        # If the particle is settled, don't move it anywhere
        if particle.settled:
            return { 'u': 0, 'v': 0, 'w': 0 }

        # If the particle is halted (but not settled), don't move it anywhere
        if particle.halted:
            return { 'u': 0, 'v': 0, 'w': 0 }

        # How far could I move?  We don't want to overshoot our desired depth.
        vertical_potential = w * modelTimestep

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
            logger.debug("DIEL: %s - Moving UP to desired depth from %f" % (self.logstring(), particle.location.depth))

            # If we are going to overshoot the desired minimum depth, 
            # calculate a new w to land in the middle of the range.
            overshoot_distance = abs(particle.location.depth - self.min_depth)
            if overshoot_distance < abs(vertical_potential):
                halfway_distance = abs((self.max_depth - self.min_depth) / 2)
                w = ((overshoot_distance - halfway_distance) / modelTimestep)

            return { 'u': u, 'v': v, 'w': w }

        """ I'm above my desired min depth, so i need to go down

            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                x                  me
            -------------------------------------- min
            -------------------------------------- max
            ______________________________________
        """
        if particle.location.depth > self.min_depth:
            logger.debug("DIEL: %s - Moving DOWN to desired depth from %f" % (self.logstring(), particle.location.depth))

            # If we are going to overshoot the desired maximum depth, 
            # calculate a new w to land in the middle of the range.
            overshoot_distance = abs(particle.location.depth - self.max_depth)
            if overshoot_distance < abs(vertical_potential):
                halfway_distance = abs((self.max_depth - self.min_depth) / 2)
                w = ((overshoot_distance - halfway_distance) / modelTimestep)

            return { 'u': u, 'v': v, 'w': -w }

        """ I'm in my desired depth, so I'm just gonna chill here

            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            -------------------------------------- min
                                x                  me
            -------------------------------------- max
            ______________________________________
        """
        return { 'u': u, 'v': v, 'w': 0 }

    def logstring(self):
        if self.pattern == self.PATTERN_CYCLE:
            return "At %s (%s%d hours) go to between %fm and %fm" % (self.cycle.upper(), self.plus_or_minus, self.time_delta, self.min_depth, self.max_depth)
        else:
            return "At %s (UTC) go to between %fm and %fm" % (self._time.strftime("%H:%M"), self.min_depth, self.max_depth)