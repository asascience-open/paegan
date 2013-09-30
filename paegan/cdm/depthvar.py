import numpy as np
import netCDF4

class Depthvar(np.ndarray):

    # How many meter in the unit
    _unit2meters={}
    _unit2meters['millimeters'] = 0.001
    _unit2meters['centimeters'] = 0.01
    _unit2meters['meters'] = 1
    _unit2meters['feet'] = 0.3048
    _unit2meters['yards'] = 0.9144
    _unit2meters['kilometers'] = 1000
    _unit2meters['miles'] = 1609.34

    # How many units in the meter
    _meters2unit={}
    _meters2unit['millimeters'] = 1000
    _meters2unit['centimeters'] = 100
    _meters2unit['meters'] = 1
    _meters2unit['feet'] = 3.2084
    _meters2unit['yards'] = 1.09361
    _meters2unit['kilometers'] = 0.001
    _meters2unit['miles'] = 0.000621371

    def __new__(self, ncfile, name, units=None, **kwargs):
        if type(ncfile) is str:
            ncfile = netCDF4.Dataset(ncfile)
        self._nc = ncfile

        data = self._nc.variables[name][:]
        if units == None:
            try:
                self._units = self._nc.variables[name].units
            except StandardError:
                self._units = 'meters'
        else:
            self._units = units

        # compatibility to CF convention v1.0/udunits names:
        if self._units in ['m','meter','meters from the sea surface']:
            self._units='meters'
        if self._units in ['cm','centimeter']:
            self._units='centimeters'
        if self._units in ['mm','millimeter']:
            self._units='millimeters'
        if self._units in ['km','kilometer']:
            self._units='kilometers'
        if self._units in ['ft','feets']:
            self._units='feet'
        if self._units in ['yd','yard']:
            self._units='yards'
        if self._units in ['mile']:
            self._units='miles'

        return data.view(self)

    def nearest_index(self, depth):
        return np.where(abs(self.meters-depth) == np.nanmin(abs(self.meters-depth)))[0]

    def nearest(self, depth):
        """
        find nearest depth,
        input and output are meters
        """
        return self.meters[self.nearest_index(depth)][0]

    def get_mm(self):
        fac = self._unit2meters[self._units] * self._meters2unit['millimeters']
        return self*fac

    def get_cm(self):
        fac = self._unit2meters[self._units] * self._meters2unit['centimeters']
        return self*fac

    def get_km(self):
        fac = self._unit2meters[self._units] * self._meters2unit['kilometers']
        return self*fac

    def get_m(self):
        fac = self._unit2meters[self._units] * self._meters2unit['meters']
        return self*fac

    meters = property(get_m, None, doc="meters")
    kilometers = property(get_km, None, doc="kilometers")
    centimeters = property(get_cm, None, doc="centimeters")
    millimeters = property(get_mm, None, doc="millimeters")
