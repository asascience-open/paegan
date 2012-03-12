import os.path
import threading
from profilehooks import profile

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
#       * We lose the first and last column of rho, U and V
#       * We lose the first and last row of rho, U and V

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


def uv_to_rho(file):
    nc = netCDF4.Dataset(file)

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
    u_data = u_data + 2

    # V
    [eta_v, xi_v] = nc.variables['lat_v'].shape
    # Don't skip any rows of V
    v_eta = range(0, eta_v)  # Y
    # Skip the first and last column of V
    v_xi = range(1, xi_v - 1)   # X
    v_data = nc.variables['v'][0,0, v_eta , v_xi ]

    # Get the angles
    angle = nc.variables['angle'][:,:]

    # Create empty rho matrix to store complex U + Vj
    U = np.empty(lat_rho.shape, dtype=complex )
    # And fill it with with nan values
    U[:] = np.nan

    # Fill rho points with averages (if we can do the calculation)
    # Thread]
    #t1 = AverageAdjacents(u_data)
    #t2 = AverageAdjacents(v_data, True)
    #t1.start(); t2.start()
    #t1.join();  t2.join()
    #u_avg = t1.data
    #v_avg = t2.data
    # Don't thread
    u_avg = average_adjacents(u_data)
    v_avg = average_adjacents(v_data,True)

    # Fill in RHO cells per diagram above.  Skip first row and first
    # column of RHOs and leave them as numpy.nan values.  Also skip the 
    # last row and column.
    U[1:rho_x-1, 1:rho_y-1] = np.vectorize(complex)(u_avg,v_avg)
    return U
    
    # We need the rotated point, so rotate by the "angle"
    #return rotate_complex_by_angle(U,angle)

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

# Threaded instance for speed testing on enormous grids.
class AverageAdjacents(threading.Thread):
    def __init__(self, data, by_column=False):
        threading.Thread.__init__(self)
        self.by_column = by_column
        self.data = data
    def data():
        return self.out
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