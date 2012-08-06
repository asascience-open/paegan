from paegan.utils.asadaylight import Daylight
from paegan.transport.location4d import Location4D
from datetime import datetime, timedelta
import pytz

class Diel(object):

    PATTERN_CYCLE        = "cycle"
    PATTERN_SPECIFICTIME = "specifictime"

    CYCLE_SUNRISE = "sunrise"
    CYCLE_SUNSET  = "sunset"

    HOURS_PLUS  = "+"
    HOURS_MINUS = "-"

    def get_pattern(self):
        return self._pattern
    def set_pattern(self, c):
        self._pattern = c
    pattern = property(get_pattern, set_pattern)

    def get_time_delta(self):
        return self._time_delta
    def set_time_delta(self, hours):
        self._time_delta = int(hours)
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
        if pom != self.HOURS_PLUS and pom != self.HOURS_MINUS:
            raise ValueError("plus_or_minus must equal '%s' or '%s'" % (self.HOURS_PLUS, self.HOURS_MINUS))
        self._plus_or_minus = pom
    plus_or_minus = property(get_plus_or_minus, set_plus_or_minus)

    def set_time(self, t):
        self._time = t
    def get_time(self, loc4d):
        """
            Based on a Location4D object and this Diel object, calculate
            the time at which this Diel migration is actually happening
        """
        if self.pattern == self.PATTERN_CYCLE:
            if loc4d is not None:
                dl = Daylight(loc=loc4d)
                if self.cycle == self.CYCLE_SUNRISE:
                    r = dl.get_ephem_rise()
                elif self.cycle == self.CYCLE_SUNSET:
                    r = dl.get_ephem_set()
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
