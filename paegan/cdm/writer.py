import numpy as np
import netCDF4 as ncd

FILL_VALUE = None

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
        t = nc.createDimension(dimname, size=dict_of_dims[dimname])
    nc.sync()
    
def add_variable(nc, varname, data, dims, compress=False, fill=FILL_VALUE):
    '''
    Thin wrapper for easily adding data to netcdf variable with just
    the variable name the current array of values, and a tuple with
    the cooresponding dimension names
    '''
    v = nc.createVariable(varname, data.dtype, dimensions=dims, zlib=compress, fill_value=fill) 
    v[:] = data
    nc.sync()

def add_scalar(nc, varname, data, compress=False, fill=FILL_VALUE):
    '''
    Functionality to simply add a scalar variable to a netcdf file,
    expects a numpy array of length 1 for the data argument.
    '''
    v = nc.createVariable(varname, data.dtype, zlib=compress, fill_value=fill)
    v[:] = data
    nc.sync()

def add_attribute(nc, key, value, var=None):
    '''
    Take in a single attname:value pair and write into the global
    or variable namespace
    '''
    if var==None:
        nc.setncattr(key, value)
    else:
        if not key in set([ "_FillValue", "_ChunkSize" ]):
            nc.variables[var].setncattr(key, value)
    nc.sync()

def add_attributes(nc, attrs, var=None):
    '''
    Take in a dict of attname:value pairs and write the whole dict
    into the global or variable namespace
    '''
    if var==None:
        nc.setncatts(attrs)
    else:
        nc.variables[var].setncatts(attrs)
    nc.sync()
