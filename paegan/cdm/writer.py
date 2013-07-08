import numpy as np
import netCDF4 as ncd

def new(filename):
    '''
    Return the netcdf4-python rootgroup for a new netcdf file
    for writing.
    '''
    return ncd.Dataset(filename, 'w', clobber=False)
    
def add_coordinates(nc, dict_of_dims):
    '''
    Create dimensions in netcdf file nc.

    >> add_coordinates(nc, {"time", (5040,)})
    '''
    # Loop through keys, and add each as a dimension, with the 
    # cooresponding dict value tuple as the representative 
    # shape of the dimension.
    for dimname in dict_of_dims.iterkeys():
        nc.createDimension(dimname, size=dict_of_dims[dimname])
    nc.sync()
    
def add_variable(nc, varname, dims, data, compress=False):
    '''
    Thin wrapper for easily adding data to netcdf variable with just
    the variable name the current array of values, and a tuple with
    the cooresponding dimension names
    '''
    nc.createVariable(varname, data.dtype, dimensions=dims, zlib=compress, fill_value=-99999) 
    nc.sync()

def add_attribute(nc, key, value, var=None):
    '''
    Take in a single attname:value pair and write into the global 
    or variable namespace
    '''
    if var==None:
        nc.setncattr(key, value)
    else:
        nc[var].setncattr(key, value)

def add_attributes(nc, attrs, var=None):
    '''
    Take in a dict of attname:value pairs and write the whole dict
    into the global or variable namespace
    '''
    if var==None:
        nc.setncatts(attrs)
    else:
        nc[var].setncatts(attrs)
    
    
