import matplotlib.pyplot as plt
from matplotlib import tri

import numpy as np
import netCDF4

from gridfield import *
import gridfield.core as gf
from gridfield.algebra import Apply, Restrict, Wrap, Bind

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
#       * We lose the first 2 and last 2 columns of the model output
#       * We lose the first 2 and last 2 rows of the model output

def subset_with_gridfields():
    URL = 'http://testbedapps-dev.sura.org/thredds/dodsC/alldata/Estuarine_Hypoxia/noaa/cbofs2/synoptic/Output_Avg/ocean_avg_synoptic_seg22.nc'

    nc = netCDF4.Dataset(URL)

    lat_u=nc.variables['lon_u']
    lon_u=nc.variables['lat_u']

    lat_v=nc.variables['lat_v']
    lon_v=nc.variables['lon_v']

    u_elements = len(lat_u[:])
    v_elements = len(lat_v[:])

    u_grid = gf.Grid("u_points")
    u_grid.setImplicit0Cells(u_elements)
    v_grid = gf.Grid("v_points")
    v_grid.setImplicit0Cells(v_elements)


def uv_to_rho():
    #URL = 'http://testbedapps-dev.sura.org/thredds/dodsC/alldata/Estuarine_Hypoxia/noaa/cbofs2/synoptic/Output_Avg/ocean_avg_synoptic_seg22.nc'
    URL = '/home/dev/Development/paegan/src/test/resources/files/ocean_avg_synoptic_seg22.nc'
    nc = netCDF4.Dataset(URL)

    lat_rho=nc.variables['lat_rho']
    lon_rho=nc.variables['lon_rho']

    # lat_rho and lon_rho should have identical shapes (eta,xi)/(y/x)
    if lat_rho.shape != lon_rho.shape:
        print "Shape of lat_rho and lon_rho must be equal"
        return None

    # Store shape for use below
    [rho_x,rho_y] = lat_rho.shape


    # Only pull the U and V values that can contribute to the averaging (see diagram).
    # This means we lost the first and last row and the first and last column.

    # U
    [eta_u, xi_u] = nc.variables['lat_u'].shape
    # Skip the first and last row of U
    u_eta = range(1, eta_u - 1)  # Y
    # Don't skip any columns of U
    u_xi = range(0, xi_u)   # X
    u_data = nc.variables['u'][0,0, u_eta , u_xi ]

    # V
    [eta_v, xi_v] = nc.variables['lat_v'].shape
    # Don't skip any rows of V
    v_eta = range(0, eta_v)  # Y
    # Skip the first and last column of V
    v_xi = range(1, xi_v - 1)   # X
    v_data = nc.variables['v'][0,0, v_eta , v_xi ]

    angle = nc.variables['angle'][:,:]

    # Create a holder for the output at RHO points.
    # We lose 4 columns and 4 rows from the averaging onto RHO points.
    # Create empty rho matrix to store complex U + Vj
    U = np.empty(lat_rho.shape, dtype=complex )
    # Fill with nan
    U[:] = np.nan

    # Fill rho points with averages (if we can do the calculation)
    # We need to transpose the U vectors because we average by column and
    # The average function averages by row.  Transpose the output back to 
    # The original.
    u_avg = average_adjacents(u_data)
    v_avg = average_adjacents(v_data, True)
    # Fill in RHO cells per diagram above.  Skip first row and first
    # column of RHOs and leave them as numpy.nan values.  Also skip the 
    # last row and column.
    U[1:rho_x-1, 1:rho_y-1] = np.vectorize(complex)(u_avg,v_avg)
    
    # We need the rotated point, so rotate by the "angle"
    U = rotate_complex_by_angle(U,angle)

    """
    print u_avg[100,100]
    print v_avg[100,100]
    print angle[100,100]
    print U[100,100]

    print u_avg[101,101]
    print v_avg[101,101]
    print angle[101,101]
    print U[101,101]
    """

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
        Sums adjacent values in a column.  Optional by_row parameter
        will sum adjacement row values.

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
        return average_adjacents(a.T).T

    try:
        [m,n] = a.shape
    except ValueError:
        [m,n] = [1,a.size]

    if m == 1:
        sumd = 0.5 * (a[0:n-1] + a[1:n])
    else:
        #sumd = 0.5 * (a[1:m,:] + a[0:m-1,:]) # By column
        sumd = 0.5 * (a[:,1:n] + a[:,0:n-1]) # By row

    return sumd

uv_to_rho()