import unittest
import numpy as np
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

if __name__ == '__main__':
    unittest.main()