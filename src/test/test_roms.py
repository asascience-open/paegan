import unittest
import numpy as np
from src import roms as rm

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
        points = np.vectorize(complex)([-0.018352,-0.0112236],[0.0125479,0.0101799])
        angles = np.array([-0.700610370006,-0.66005638354])
        r = rm.rotate_complex_by_angle(points,angles)
        result_test = np.array([0.00653817652156+0.00291860800465j, -0.00680340220893+0.0211650552343j ], dtype=complex)

        assert np.allclose(r,result_test)

if __name__ == '__main__':
    unittest.main()