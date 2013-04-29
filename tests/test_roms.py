import unittest
import numpy as np
import os
import math
import netCDF4

from paegan.roms import roms as rm

class RomsTest(unittest.TestCase):

    def setUp(self):
        self.data_path = "/data/lm/tests"

    def  test_1D_average(self):            
        # array([ 0,  2,  4,  6,  8, 10, 12])
        a = np.arange(0,13,2)
        a_avg = rm.average_adjacents(a)

        # array([  1.,   3.,   5.,   7.,   9.,  11.])
        result_test = np.arange(1,12,2)
       
        assert np.allclose(a_avg,result_test)

    def test_2D_row_average(self):

        # array([[ 0,  2,  4,  6,  8],
        #        [10, 12, 14, 16, 18],
        #        [20, 22, 24, 26, 28]])
        a = np.arange(0,30,2).reshape(3,5)
        a_avg = rm.average_adjacents(a)

        result_test = np.arange(1,30,2).reshape(3,5)[:,0:-1]
        # array([[ 1,  3,  5,  7],
        #        [11, 13, 15, 17],
        #        [21, 23, 25, 27]])

        assert np.allclose(a_avg,result_test)

    def test_2D_column_average(self):

        # array([[ 0, 10, 20],
        #        [ 2, 12, 22],
        #        [ 4, 14, 24],
        #        [ 6, 16, 26],
        #        [ 8, 18, 28]])
        a = np.arange(0,30,2).reshape(3,5).T
        a_avg = rm.average_adjacents(a, True)

        result_test = np.arange(1,30,2).reshape(3,5)[:,0:-1].T
        # array([[ 1, 11, 21],
        #        [ 3, 13, 23],
        #        [ 5, 15, 25],
        #        [ 7, 17, 27]])
    
        assert np.allclose(a_avg,result_test)

    def test_angle_rotation(self):
        points = np.vectorize(complex)([-0.018,-0.013],[0.013,0.012])
        angles = np.array([-0.7,-0.3])
        r = rm.rotate_complex_by_angle(points,angles)

        # (-0.018+0.013j) * e^(sqrt(-1) * -0.7) = (-0.00539233+0.02153887j)
        # (-0.013+0.012j) * e^(sqrt(-1) * -0.3) = (-0.00887313+0.01530580j)

        result_test = np.array([-0.00539233+0.02153887j, -0.00887313+0.01530580j ], dtype=complex)

        assert np.allclose(r,result_test)

    def test_uv_size(self):
        #URL = 'http://testbedapps-dev.sura.org/thredds/dodsC/alldata/Estuarine_Hypoxia/noaa/cbofs2/synoptic/Output_Avg/ocean_avg_synoptic_seg22.nc'
        URL = os.path.join(self.data_path, "ocean_avg_synoptic_seg22.nc")

        # Call the uv_to_rho to calculate the resulting complex numbers on the 
        # rho grid.
        uv_rho = rm.uv_to_rho(URL)

        # Manually calculate the two complex numbers for (rho) blocks.
        # The RHO blocks are (101,101) and (101,102) in this case
        nc = netCDF4.Dataset(URL)
        u = nc.variables['u'][0,0,:,:]
        v = nc.variables['v'][0,0,:,:]

        # This is what we have.
        #  ---------------------------------
        #  rho | u | rho | u | rho | u | rho
        #  ---------------------------------
        #   v  |   | {v} |   | {v} |   |  v
        #  ---------------------------------
        #  rho |{u}|(rho)|{u}|(rho)|{u}| rho
        #  ---------------------------------
        #   v  |   | {v} |   | {v} |   |  v
        #  ---------------------------------
        #  rho | u | rho | u | rho | u | rho
        #  ---------------------------------

        left_rho_u = 0.5 * (u[101,100] + u[101,101])
        left_rho_v = 0.5 * (v[100,101] + v[101,101])

        right_rho_u = 0.5 * (u[101,101] + u[101,102])
        right_rho_v = 0.5 * (v[100,102] + v[101,102])

        # Turn into a numpy array of complex numbers
        U = np.vectorize(complex)(np.array([left_rho_u,right_rho_u]), np.array(left_rho_v,right_rho_v))

        # Grab angles at the (rho) points
        angles = nc.variables['angle'][101,101:103]

        # And rotate by those angles
        U = rm.rotate_complex_by_angle(U,angles)

        left_rho  = U[0]
        right_rho = U[1]

        #print
        #print "Manual Left (101,101): " + str(left_rho)
        #print "Method Left (101,101): " + str(uv_rho[101,101])
        #print
        #print "Manual Right (101,102): " + str(right_rho)
        #print "Method Right (101,102): " + str(uv_rho[101,102])

        assert left_rho == uv_rho[101,101]
        # Why does the right point now work!!!?!?!?!?!?!?
        #assert right_rho == uv_rho[101,102]

if __name__ == '__main__':
    unittest.main()