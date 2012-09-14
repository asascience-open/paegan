import sys, os, bisect, netCDF4
import numpy as np
try:
    from osgeo import gdal
except:
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
            lat = run.variables['lat'][:]
            lon = run.variables['lon'][:]
            column_i = bisect.bisect(xarray, lon).flatten()
            row_i = bisect.bisect(yarray, lat).flatten()
            for i in row_i:
                for j in column_i:
                    prob[i, j] += 1
        shape = lat.shape
        prob = prob / (shape[0] * shape[1] * len(trajectory_files)) # Assumes same # of particles
                                                                    # for every run, may be bad
                                                                    # assumtion
    elif method=='run':
        prob = []
        for i, runfile in enumerate(trajectory_files):
            prob.append(np.zeros((ny, nx)))
            run = netCDF4.Dataset(runfile)
            lat = run.variables['lat'][:]
            lon = run.variables['lon'][:]
            column_i = bisect.bisect(xarray, lon).flatten()
            row_i = bisect.bisect(yarray, lat).flatten()
            for i in row_i:
                for j in column_i:
                    if prob[i][i, j] == 0:
                        prob[i][i, j] += 1
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
    prob = compute_probability(**kwargs)
    
    tiff = gdal.GetDriverByName('GTiff')
    rasterout = tiff.Create(outputname + '.tif', kwargs.get('nx'), 
                            kwargs.get('ny'), 1, gdal.GDAL_Float32)
    raster_xfrm = []
    rasterout.SetGepTransform(raster_xfrm)
    rasterout.SetProjection(r'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]')
    rasterout.GetRasterBand(1).WriteArray(prob)
    
