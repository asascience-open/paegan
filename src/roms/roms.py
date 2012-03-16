import os.path
import threading
import numpy as np
import netCDF4

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

    # U ]
    u_data = nc.variables['u'][0,0,:,:]

    # V
    v_data = nc.variables['v'][0,0,:,:]

    # Get the angles
    angle = nc.variables['angle'][:,:]

    # Create empty rho matrix to store complex U + Vj
    U = np.empty([rho_y,rho_x], dtype=complex )
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
    vfunc = np.vectorize(complex)
    # Only pull the U and V values that can contribute to the averaging (see diagram).
    # This means we lost the first and last row and the first and last column of both
    # U and V.
    complexed = vfunc(u_avg[1:-1,:],v_avg[:,1:-1])
    U[1:rho_y-1, 1:rho_x-1] = complexed
 
    # We need the rotated point, so rotate by the "angle"
    return rotate_complex_by_angle(U,angle)

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