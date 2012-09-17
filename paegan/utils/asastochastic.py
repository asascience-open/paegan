import sys, os, bisect, netCDF4, math
import numpy as np
try:
    from osgeo import gdal
    from osgeo import osr
except:
    import osr
    import gdal

def compute_probability(trajectory_files, bbox=None, 
                        nx=None, ny=None, method='overall'):
    """
        This function creates a probability (stochastic) grid 
        for trajectory model data using 'overall' method (based
        on normalization by nsteps * nparticles) or 'run' method
        (based on normalization by run).
        
        probability_grid = compute_probability([myfile1.nc, myfile2.nc],
                                               bbox = [-75, 23, -60, 45],
                                               nx = 1000, ny = 1000,
                                               method = 'overall')  
    """
    xarray = np.linspace(float(bbox[0]), float(bbox[2]), int(nx)+1) 
    yarray = np.linspace(float(bbox[1]), float(bbox[3]), int(ny)+1)
    if method=='overall':
        prob = np.zeros((ny, nx))
        for runfile in trajectory_files:
            run = netCDF4.Dataset(runfile)
            lat = run.variables['lat'][:].flatten()
            lon = run.variables['lon'][:].flatten()
            column_i, row_i = [], []
            for clon, clat in zip(lon, lat):
                column_i.append(bisect.bisect(xarray, clon))
                row_i.append(bisect.bisect(yarray, clat))
                try:
                    prob[row_i[-1], column_i[-1]] += 1
                except:
                    pass
        shape = lat.shape
        prob = prob / (shape[0] * len(trajectory_files)) # Assumes same # of particles
                                                         # for every run, may be bad
                                                         # assumtion
    elif method=='run':
        prob = []
        for i, runfile in enumerate(trajectory_files):
            prob.append(np.zeros((ny, nx)))
            run = netCDF4.Dataset(runfile)
            lat = run.variables['lat'][:].flatten()
            lon = run.variables['lon'][:].flatten()
            column_i, row_i = [], []
            for clon, clat in zip(lon, lat):
                column_i.append(bisect.bisect(xarray, clon))
                row_i.append(bisect.bisect(yarray, clat))
                try:
                    if prob[i][row_i[-1], column_i[-1]] == 0:
                        prob[i][row_i[-1], column_i[-1]] = 1
                except:
                    pass
        prob2 = np.zeros((ny, nx))
        for run in prob:
            prob2 = run + prob2
        prob = prob2 / len(prob)
    return prob
    
def export_probability(outputname, **kwargs):
    """
        Calculate probability and export to gis raster/grid
        format. 
        
        export_probability(prob_out,
                           trajectory_files = [myfiles1.nc, myfiles2.nc],
                           bbox = [-75, 23, -60, 45],
                           nx = 1000, ny = 1000,
                           method = 'overall')  
    """
    bbox = kwargs.get('bbox', None)
    nx, ny = kwargs.get('nx', None), kwargs.get('ny', None)
    if bbox == None:
        raise ValueError('Must supply bbox keyword argument.')
    if nx == None or ny == None:
        raise ValueError('Must supply nx and ny keyword arguments.')
    
    prob = compute_probability(**kwargs)

    xres = (float(bbox[2]) - float(bbox[0])) / float(nx)
    yres = (float(bbox[3]) - float(bbox[1])) / float(ny)
    tiff = gdal.GetDriverByName('GTiff')
    rasterout = tiff.Create(outputname + '.tif', nx, 
                            ny, 1, gdal.GDT_Float32)
    raster_xfrm = [float(bbox[0]), xres, 0.0, float(bbox[3]), 0.0, -yres]
    rasterout.SetGeoTransform(raster_xfrm)
    srs = osr.SpatialReference()
    srs.SetWellKnownGeogCS( 'WGS84' )
    rasterout.SetProjection( srs.ExportToWkt() )
    rasterout.GetRasterBand(1).WriteArray(prob[::-1, :])
    
