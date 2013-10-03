import os.path
import threading
import numpy as np
import netCDF4
from paegan.utils.asainterpolate import CfGeoInterpolator
import paegan.cdm.writer as pw
from collections import OrderedDict
import datetime

#       ---------------------------------
#       rho | u | rho | u | rho | u | rho
#       ---------------------------------
#        v  |   | {v} |   | {v} |   |  v
#       ---------------------------------
#       rho |{u}|(rho)|{u}|(rho)|{u}| rho
#       ---------------------------------
#        v  |   | {v} |   | {v} |   |  v
#       ---------------------------------
#       rho | u | rho | u | rho | u | rho
#       ---------------------------------
#
#       Assumes:
#       size(rho)=ny,nx;   size(u)=ny,nx-1;   size(v)=ny-1,nx
#       coordinate dimension: t,z,y,x
#
#       When Averaging U and V into the RHO grid:
#       * We lose the first and last column of rho and V
#       * We lose the first and last row of rho and U

def shrink(a, b):
    """
    Ripped from Octant: https://code.google.com/p/octant

    Return array shrunk to fit a specified shape by triming or averaging.

    a = shrink(array, shape)

    array is an numpy ndarray, and shape is a tuple (e.g., from
    array.shape). a is the input array shrunk such that its maximum
    dimensions are given by shape. If shape has more dimensions than
    array, the last dimensions of shape are fit.

    as, bs = shrink(a, b)

    If the second argument is also an array, both a and b are shrunk to
    the dimensions of each other. The input arrays must have the same
    number of dimensions, and the resulting arrays will have the same
    shape.

    Example
    -------

    >>> shrink(rand(10, 10), (5, 9, 18)).shape
    (9, 10)
    >>> map(shape, shrink(rand(10, 10, 10), rand(5, 9, 18)))
    [(5, 9, 10), (5, 9, 10)]

    """

    if isinstance(b, np.ndarray):
        if not len(a.shape) == len(b.shape):
            raise Exception, \
                  'input arrays must have the same number of dimensions'
        a = shrink(a,b.shape)
        b = shrink(b,a.shape)
        return (a, b)

    if isinstance(b, int):
        b = (b,)

    if len(a.shape) == 1:                # 1D array is a special case
        dim = b[-1]
        while a.shape[0] > dim:          # only shrink a
            if (dim - a.shape[0]) >= 2:  # trim off edges evenly
                a = a[1:-1]
            else:                        # or average adjacent cells
                a = 0.5*(a[1:] + a[:-1])
    else:
        for dim_idx in range(-(len(a.shape)),0):
            dim = b[dim_idx]
            a = a.swapaxes(0,dim_idx)        # put working dim first
            while a.shape[0] > dim:          # only shrink a
                if (a.shape[0] - dim) >= 2:  # trim off edges evenly
                    a = a[1:-1,:]
                if (a.shape[0] - dim) == 1:  # or average adjacent cells
                    a = 0.5*(a[1:,:] + a[:-1,:])
            a = a.swapaxes(0,dim_idx)        # swap working dim back

    return a

def _uv_to_rho(u_data, v_data, angle, rho_x, rho_y):
    # Create empty rho matrix to store complex U + Vj
    U = np.empty([rho_y,rho_x], dtype=complex )
    # And fill it with with nan values
    U[:] = np.nan

    vfunc = np.vectorize(complex)

    # THREE IDENTICAL METHODS
    # Fill in RHO cells per diagram above.  Skip first row and first
    # column of RHOs and leave them as numpy.nan values.  Also skip the
    # last row and column.

    #1.)
    # Fill rho points with averages (if we can do the calculation)
    # Thread]
    #t1 = AverageAdjacents(u_data)
    #t2 = AverageAdjacents(v_data, True)
    #t1.start(); t2.start()
    #t1.join();  t2.join()
    #u_avg = t1.data
    #v_avg = t2.data
    #complexed = vfunc(u_avg[1:-1,:],v_avg[:,1:-1])

    # 2.)
    # Don't thread
    u_avg = average_adjacents(u_data)
    v_avg = average_adjacents(v_data,True)
    complexed = vfunc(u_avg[1:-1,:],v_avg[:,1:-1])

    # 3.)
    # Use Octant method
    #data_U = (rho_y-2,rho_x-2)
    #u_avg = shrink(u_data, data_U)
    #v_avg = shrink(v_data, data_U)
    #complexed = vfunc(u_avg,v_avg)

    # Only pull the U and V values that can contribute to the averaging (see diagram).
    # This means we lost the first and last row and the first and last column of both
    # U and V.
    U[1:rho_y-1, 1:rho_x-1] = complexed

    # We need the rotated point, so rotate by the "angle"
    return rotate_complex_by_angle(U,angle)

def uv_to_rho(file):
    nc = netCDF4.Dataset(file)

    lat_rho=nc.variables['lat_rho']
    lon_rho=nc.variables['lon_rho']

    # lat_rho and lon_rho should have identical shapes (eta,xi)/(y/x)
    if lat_rho.shape != lon_rho.shape:
        print "Shape of lat_rho and lon_rho must be equal"
        return None

    # Store shape for use below
    [rho_y,rho_x] = lat_rho.shape

    # U
    u_data = nc.variables['u'][0,0,:,:]

    # V
    v_data = nc.variables['v'][0,0,:,:]

    # Get the angles
    angle = nc.variables['angle'][:,:]

    # Close the dataset
    nc.close()

    return _uv_to_rho(u_data, v_data, angle, rho_x, rho_y)

def rotate_complex_by_angle(points,angles):
    """
        points: ND array of complex numbers
        angles: ND array of angles, same size as points

        Multiply the points we have (stored as complex) by another complex number
        whose angle with the positive X axis is the angle we need to rotate by.

        np.exp(1J*angle)  creates an array the same size of U filled with complex numbers
                          that represent the angled points from X axis.
    """
    return points * np.exp(1j*angles)

def average_adjacents(a, by_column=False):
    """
        Sums adjacent values in a column.  Optional by_column parameter
        will sum adjacement column values.

        For a row that looks like this:
        [ 2, 4, 6, 8, 10, 12 ]

        The following addition is computed:

        [ 2, 4, 6,  8, 10 ]
                +
        [ 4, 6, 8, 10, 12 ]

        Resulting in

        [ 3, 5, 7, 9, 11 ]

        Use:

            # 1D Array
            >>> a = np.arange(0,13,2)
            >>> a
            array([ 0,  2,  4,  6,  8, 10, 12])

            >>> a_avg = average_adjacents(a)
            >>> a_avg
            array([  1.,   3.,   5.,   7.,   9.,  11.])


            # 2D Array
            >>> a = np.arange(0,30,2).reshape(3,5)
            >>> a
            array([[ 0,  2,  4,  6,  8],
                   [10, 12, 14, 16, 18],
                   [20, 22, 24, 26, 28]])
            >>> a_avg = average_adjacents(a)
            >>> a_avg
            array([[  1,  3,  5,  7],
                   [ 11, 13, 15, 17],
                   [ 21, 23, 25, 27]])


            # 2D Array, by column
            >>> a = np.arange(0,30,2).reshape(3,5)
            >>> a
            array([[ 0,  2,  4,  6,  8],
                   [10, 12, 14, 16, 18],
                   [20, 22, 24, 26, 28]])
            >>> a_avg = average_adjacents(a, True)
            >>> a_avg
            array([[  5.,   7.,   9.,  11.,  13.],
                   [ 15.,  17.,  19.,  21.,  23.]])

    """
    if by_column:
        # Easier to transpose, sum by row, and transpose back.
        #sumd = 0.5 * (a[1:m,:] + a[0:m-1,:])
        return average_adjacents(a.T).T

    try:
        [m,n] = a.shape
    except ValueError:
        [m,n] = [1,a.size]

    if m == 1:
        sumd = 0.5 * (a[0:n-1] + a[1:n]) # Single row
    else:
        sumd = 0.5 * (a[:,0:n-1] + a[:,1:n]) # By row

    return sumd

def regrid_roms(newfile, filename, lon_new, lat_new, t=None, z=None):
    '''Function to regrid the entire roms datasets (all values on non-rho coords)
       onto an arbitrary grid to support regridding on to regular grids as well.
    '''
    with pw.new(newfile) as new:
        with netCDF4.Dataset(filename) as nc:
            for key in nc.variables:
                try:
                    if "since" in nc.variables[key].units:
                        time = nc.variables[key][:]
                except AttributeError:
                    pass
            # Identify the rho coordinates, and get them
            lon_rho = nc.variables["lon_rho"][:]
            lat_rho = nc.variables["lat_rho"][:]
            rho_y, rho_x = lat_rho.shape
            depth_rho = nc.variables["s_rho"][:]
            #depth_w   = nc.variables["s_w"][:]
            if t == None:
                t = time
            # Put dimensions into the new netcdf file, should only be for
            # time, rhos, psis (not sure what to do about w yet)
            if len(depth_rho.shape) == 4:
                s_rho = depth_rho.shape[1]
            else:
                s_rho = depth_rho.shape[0]
            if len(lon_new.shape) == 2 and len(lon_new.shape) == 2:
                eta_new = lat_new.shape[0]
                xi_new = lon_new.shape[1]
            elif len(lon_new.shape) == 1 and len(lon_new.shape) == 1:
                eta_new = lat_new.shape[0]
                xi_new = lon_new.shape[0]
            else:
                raise ValueError("New lat and lon have invalid shapes or don't match in shape.")
            if z == None:
                z = depth_rho
            s_new = z.shape[0]
            time_new = t.shape[0]

            #[pw.add_attribute(new, at, new.getncattr(at)) for at in new.ncattrs()]
            pw.add_coordinates(new, OrderedDict([("time_new",time_new),("s_new",s_new),("eta_new",eta_new),("xi_new",xi_new)]))
            #print "Coordinates " + str([("time_new",time_new),("s_new",s_new),("eta_new",eta_new),("xi_new",xi_new)])

            pw.add_variable(new, "ocean_time", t, ("time_new",))
            pw.add_variable(new, "s_new", z, ("s_new",))
            if len(lon_new.shape) == 2 and len(lat_new.shape) == 2:
                pw.add_variable(new, "lat_new", lat_new, ("eta_new", "xi_new",))
                pw.add_variable(new, "lon_new", lon_new, ("eta_new", "xi_new",))
            elif len(lon_new.shape) == 1 and len(lat_new.shape) == 1:
                pw.add_variable(new, "lat_new", lat_new, ("eta_new",))
                pw.add_variable(new, "lon_new", lon_new, ("xi_new",))
            # Identify variables that arn't coordinates, and their native grids,
            # convert non-rho variables to rho with `average_adjacents`. Create
            # sequence of rho-based variables in `roms_variables` object
            for key in nc.variables:
                var = nc.variables[key]
                try:
                    if key == "w":
                        if z == None:
                            z = depth_w
                        grid_type = "rho"
                    else:
                        if "_psi" in var.coordinates:
                            grid_type = "psi"
                        elif "_u" in var.coordinates:
                            grid_type = "u"
                        elif "_v" in var.coordinates:
                            grid_type = "v"
                        else:
                            grid_type = "rho"
                except AttributeError:
                    grid_type = None
                if grid_type != None and grid_type != "psi":
                    if key in set([ "sustr", "bustr", "DU_avg1", "DU_avg2", "u", "w", "ubar", "mask_u", "mask_v", "mask_psi", "mask_rho" ]):
                        pass
                    elif grid_type == "v":
                        var_dimensionality = len(var.shape)
                        if "sv" in key or "bv" in key or "DV" in key or key == "vbar" or key == "v":
                            paired_vector = {"svstr":"sustr", 
                                             "bvstr":"bustr", 
                                             "DV_avg1":"DU_avg1", 
                                             "DV_avg2":"DU_avg2",
                                             "vbar":"ubar",
                                             "v":"u"}
                            for i in xrange(var.shape[0]):
                                if var_dimensionality == 3:
                                    complex_uv = _uv_to_rho(nc.variables[paired_vector[key]][i,:,:], var[i,:,:], nc.variables["angle"][:], rho_x, rho_y)
                                    uz, vz = complex_uv.real, complex_uv.imag
                                elif var_dimensionality == 4:
                                    for j in xrange(var.shape[1]):
                                        complex_uv = _uv_to_rho(nc.variables["u"][i,j,:,:], var[i,j,:,:], nc.variables["angle"][:], rho_x, rho_y)
                                        if j == 0:
                                            uz, vz = complex_uv.real[np.newaxis,:], complex_uv.imag[np.newaxis,:]
                                        else:
                                            uz = np.vstack((uz, complex_uv.real[np.newaxis,:]))
                                            vz = np.vstack((vz, complex_uv.imag[np.newaxis,:]))
                                if i == 0:
                                    u, v = uz[np.newaxis,:], vz[np.newaxis,:]
                                else:
                                    u = np.vstack((u, uz[np.newaxis,:]))
                                    v = np.vstack((v, vz[np.newaxis,:]))
                            values = {paired_vector[key]:u, key:v}
                            for new_key in values:
                                values_interp[:, np.where(nc.variables["mask_rho"]==0)] = np.nan
                                if var_dimensionality == 3:
                                    interpolator = CfGeoInterpolator(values[new_key], lon_rho, lat_rho, t=time)
                                    values_interp = interpolator.interpgrid(lon_new, lat_new, t=t)
                                    coordtuple = ("time_new", "eta_new", "xi_new",)
                                    coordattr = "ocean_time lat_new lon_new"
                                elif var_dimensionality == 4:
                                    interpolator = CfGeoInterpolator(values[new_key], lon_rho, lat_rho, t=time, z=depth_rho)
                                    values_interp = interpolator.interpgrid(lon_new, lat_new, t=t, z=z)
                                    coordtuple = ("time_new", "s_new", "eta_new", "xi_new",)
                                    coordattr = "ocean_time s_new lat_new lon_new"
                                values_interp = np.ma.MaskedArray(values_interp, mask=values_interp==np.nan)
                                pw.add_variable(new, new_key, values_interp, coordtuple)
                                [pw.add_attribute(new, at, nc.variables[new_key].getncattr(at), var=new_key) for at in nc.variables[new_key].ncattrs()]
                                pw.add_attribute(new, "coordinates", coordattr, var=new_key)
                    else:
                        var_dimensionality = len(var.shape)
                        vartmp = var[:]
                        if var_dimensionality == 4:
                            vartmp[:,:, np.where(nc.variables["mask_rho"]==0)] = np.nan
                            interpolator = CfGeoInterpolator(vartmp, lon_rho, lat_rho, t=time, z=depth_rho)
                            values_interp = interpolator.interpgrid(lon_new, lat_new, t=t, z=z)
                            pw.add_variable(new, key, values_interp, ("time_new", "s_new", "eta_new", "xi_new",))
                            [pw.add_attribute(new, at, nc.variables[key].getncattr(at), var=key) for at in nc.variables[key].ncattrs()]
                            pw.add_attribute(new, "coordinates", "ocean_time s_new lat_new lon_new", var=key)
                        elif var_dimensionality == 3:
                            vartmp[:, np.where(nc.variables["mask_rho"]==0)] = np.nan
                            if var.shape[0] == time.shape[0]:
                                try:
                                    interpolator = CfGeoInterpolator(vartmp, lon_rho, lat_rho, t=time)
                                    values_interp = interpolator.interpgrid(lon_new, lat_new, t=t)
                                    values_interp = np.ma.MaskedArray(values_interp, mask=values_interp==np.nan)
                                    pw.add_variable(new, key, values_interp, ("time_new", "eta_new", "xi_new",))
                                    [pw.add_attribute(new, at, nc.variables[key].getncattr(at), var=key) for at in nc.variables[key].ncattrs()]
                                    pw.add_attribute(new, "coordinates", "ocean_time lat_new lon_new", var=key)
                                except:
                                    print key, vartmp.shape, lon_rho.shape, lat_rho.shape, time.shape
                            elif var.shape[0] == depth_rho.shape[0]:
                                interpolator = CfGeoInterpolator(vartmp, lon_rho, lat_rho, z=depth_rho)
                                values_interp = interpolator.interpgrid(lon_new, lat_new, z=z)
                                values_interp = np.ma.MaskedArray(values_interp, mask=values_interp==np.nan)
                                pw.add_variable(new, key, values_interp, ("depth_new", "eta_new", "xi_new",))
                                [pw.add_attribute(new, at, nc.variables[key].getncattr(at), var=key) for at in nc.variables[key].ncattrs()]
                                pw.add_attribute(new, "coordinates", "s_new lat_new lon_new", var=key)
                            else:
                                raise valueerror("unsure about what dimension this varaible varies with in addition to lat/lon.")
                        elif var_dimensionality == 2:
                            vartmp[np.where(nc.variables["mask_rho"]==0)] = np.nan
                            interpolator = CfGeoInterpolator(vartmp, lon_rho, lat_rho)
                            values_interp = interpolator.interpgrid(lon_new, lat_new)
                            values_interp = np.ma.MaskedArray(values_interp, mask=values_interp==np.nan)
                            pw.add_variable(new, key, values_interp, ("eta_new", "xi_new",))
                            [pw.add_attribute(new, at, nc.variables[key].getncattr(at), var=key) for at in nc.variables[key].ncattrs()]
                            pw.add_attribute(new, "coordinates", "lat_new lon_new", var=key)
                        else:
                            # todo if 1-d check for which dimension it matches and interp based on that...
                            #      if 5+ d, only interpolate to the 4d dimensions that we can specify i guess...
                            raise valueerror("sort of confused about the dimensionality of the variable i am attempting to regrid...")
                elif grid_type == "psi":
                    pass
                else:
                    if len(var.dimensions) == 0:
                        pw.add_scalar(new, key, var[:])
                        [pw.add_attribute(new, at, nc.variables[key].getncattr(at), var=key) for at in nc.variables[key].ncattrs()]

            # Add time attributes
            for key in nc.variables:
                var = nc.variables[key]
                if "time" in key:
                    [pw.add_attribute(new, at, nc.variables[key].getncattr(at), var="ocean_time") for at in nc.variables[key].ncattrs()]

            # Add global attributes to the file
            [pw.add_attribute(new, at, nc.getncattr(at)) for at in nc.ncattrs()]
            try:
                new.history = new.history + ", regridded by Python tool 'paegan' at " + str(datetime.datetime.now())
            except:
                new.history = "regridded by Python tool 'paegan' at " + str(datetime.datetime.now())
        new.sync()

# Threaded instance for speed testing on enormous grids.
class AverageAdjacents(threading.Thread):
    def __init__(self, data, by_column=False):
        threading.Thread.__init__(self)
        self.by_column = by_column
        self.data = data
    def run(self):
        if self.by_column:
            # Easier to transpose, sum by row, and transpose back.
            #sumd = 0.5 * (a[1:m,:] + a[0:m-1,:])
            t3 = AverageAdjacents(self.data.T)
            t3.start(); t3.join()
            self.data = t3.data.T
            return

        try:
            [m,n] = self.data.shape
        except ValueError:
            [m,n] = [1,self.data.size]

        if m == 1:
            sumd = 0.5 * (self.data[0:n-1] + self.data[1:n]) # Single row
        else:
            sumd = 0.5 * (self.data[:,0:n-1] + self.data[:,1:n]) # By row

        self.data = sumd
        return

