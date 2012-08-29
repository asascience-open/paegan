# encoding: utf-8

# Pulled from Octant
# http://code.google.com/p/octant/source/browse/trunk/octant/ocean/time.py
# Copyright (c) 2006 Robert Hetland & Richard Hofmeister

import numpy as np
import netCDF4, datetime
from dateutil.parser import parse
import pylab
import bisect

class Timevar(np.ndarray):
    
    _unit2sec={}
    _unit2sec['seconds'] = 1.0
    _unit2sec['minutes'] = 60.0
    _unit2sec['hours'] = 3600.0
    _unit2sec['days'] = 3600.0*24.0
    _unit2sec['weeks'] = 3600.0*24.0*7.0
    _unit2sec['years'] = 3600.0*24.0*365.242198781 #ref to udunits

    _sec2unit={}
    _sec2unit['seconds'] = 1.0
    _sec2unit['minutes'] = 1.0/60.0
    _sec2unit['hours'] = 1.0/3600.0
    _sec2unit['days'] = 1.0/(24.0*3600.0)

    def __new__(self, ncfile, name='time', units=None, **kwargs):
        if type(ncfile) is str:
            ncfile = netCDF4.Dataset(ncfile)
        self._nc = ncfile
        
        if self._nc.variables[name].ndim > 1:
            _str_data = self._nc.variables[name][:,:]
            if units == None:
                units = 'seconds since 1990-01-01'
            dates = [parse(_str_data[i, :].tostring()) for i in range(len(_str_data[:,0]))]
            data = netCDF4.date2num(dates, units)
        else:
            data = self._nc.variables[name][:]
            
        if units == None:
            try:
                self._units = self._nc.variables[name].units
            except:
                self._units = units
        else:
            self._units = units
        
        units_split=self._units.split(' ',2)
        assert len(units_split) == 3 and units_split[1] == 'since', \
            'units string improperly formatted\n' + self._units
        self.origin=parse(units_split[2])
        
        self._units = units_split[0].lower()
        
        # compatibility to CF convention v1.0/udunits names:
        if self._units in ['second','sec','secs','s']:
            self._units='seconds'
        if self._units in ['min','minute','mins']:
            self._units='minutes'
        if self._units in ['h','hs','hr','hrs','hour']:
            self._units='hours'
        if self._units in ['day','d','ds']:
            self._units='days'

        return data.view(self)
    
    def gettimestep(self):
        return self.seconds[1] - self.seconds[0]
    
    def nearest_index(self, dateo, select='nearest'):
        to = pylab.date2num(dateo)
        if select == 'nearest':
            try:
                return [np.where(abs(self.jd-t) == min(abs(self.jd-t)))[0][0] for t in to]
            except TypeError:
                return [np.where(abs(self.jd-to) == min(abs(self.jd-to)))[0][0]]
        elif select == 'before':
            try: 
                return np.asarray([bisect.bisect(self.jd, t)-1 for t in to])
            except TypeError:
                return np.asarray([bisect.bisect(self.jd, to)-1])
    
    def nearest(self, dateo):
        """
        find nearest model timestep,
        input and output are datetime objects
        """
        # one might choose the second value for 
        #if len(self.nearest_index(dateo)) == 1:
        #    res=self.jd[self.nearest_index(dateo)][0]
        #else:
        #    res=self.jd[self.nearest_index(dateo)][1]
        return pylab.num2date(self.jd[self.nearest_index(dateo)][0])
    
    def get_seconds(self):
        fac = self._unit2sec[self._units] * self._sec2unit['seconds']
        return self*fac
    
    def get_minutes(self):
        fac = self._unit2sec[self._units] * self._sec2unit['minutes']
        return self*fac

    def get_hours(self):
        fac = self._unit2sec[self._units] * self._sec2unit['hours']
        return self*fac
    
    def get_days(self):
        fac = self._unit2sec[self._units] * self._sec2unit['days']
        return np.asarray(self,dtype='float64')*fac
    
    def get_jd(self):
        return (pylab.date2num(self.origin)+self.days)

    def get_dates(self):
        return np.asarray(pylab.num2date(self.jd))
        
    jd = property(get_jd, None, doc="Julian day, for plotting in pylab")
    seconds = property(get_seconds, None, doc="seconds")
    minutes = property(get_minutes, None, doc="minutes")
    hours = property(get_hours, None, doc="hours")
    days = property(get_days, None, doc="days")
    dates = property(get_dates, None, doc="datetime objects")
    timestep = property(gettimestep, None)
