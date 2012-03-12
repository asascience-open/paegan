import unittest
import numpy as np
import os
import math

from src.roms import roms as rm

class RomsTest(unittest.TestCase):

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
        URL = os.path.normpath(os.path.join(os.path.dirname(__file__),"./resources/files/ocean_avg_synoptic_seg22.nc"))

        # From file
        # http://testbedapps-dev.sura.org/thredds/dodsC/alldata/Estuarine_Hypoxia/noaa/cbofs2/synoptic/Output_Avg/ocean_avg_synoptic_seg22.nc.ascii?u[0:1:0][0:1:0][100:1:101][99:1:102],v[0:1:0][0:1:0][99:1:101][100:1:102],angle[100:1:102][100:1:103]
        #
        # U / V
        # ---------------------------------------------------------------------------------------------------------------
        #      rho     | 0.00103918 |         rho         | -0.00214493 |          rho        | 0.02839777 |    rho
        # ---------------------------------------------------------------------------------------------------------------
        #  0.00497477  |            |     0.00125827      |             |      -0.00457699    |            | 0.00461918
        # ---------------------------------------------------------------------------------------------------------------
        #      rho     | 0.01185319 |        (rho)        | 0.01215537  |         (rho)       | 0.01831482 |    rho
        #              |            | -0.6600563835401998 |             | -0.6384198811416639 |            |
        # ---------------------------------------------------------------------------------------------------------------
        #  -0.01828926 |            |     -0.01866616     |             |     -0.01803783     |            | -0.01132555
        # ---------------------------------------------------------------------------------------------------------------
        #      rho     | 0.01286777 |         rho         | 0.01294046  |          rho        | 0.01156001 |    rho
        # ---------------------------------------------------------------------------------------------------------------

        uv_rho = rm.uv_to_rho(URL)
        #print uv_rho[95:105,95:105]
        left_rho_u = 0.5 * (0.01185319 + 0.01215537)
        left_rho_v = 0.5 * (0.00125827 + -0.01866616)
        right_rho_u = 0.5 * (0.01215537 + 0.01831482)
        right_rho_v = 0.5 * (-0.00457699 + -0.01803783)

        left_rho  = (complex)(left_rho_u,left_rho_v)# * math.e**(1j * -0.6600563835401998)
        right_rho = (complex)(right_rho_u,right_rho_v)# *  math.e**(1j * -0.6384198811416639)

        print left_rho
        print right_rho


if __name__ == '__main__':
    unittest.main()