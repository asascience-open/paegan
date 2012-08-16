===========
Paegan - Processing and Analysis of Geophysics And Numbers
===========

Try it out
==========

1. Install Python 2.7.x

2. Install GDAL with python support
    $ wget http://download.osgeo.org/gdal/gdal-1.9.1.tar.gz
    $ tar zxvf gdal-1.9.1.tar.gz
    $ cd gdal-1.9.1
    $ ./configure; make
    $ make install

3. Install the HDF5 and NetCDF4 Libraries

4. Set the HDF5_DIR and NETCDF4_DIR environmental variables

5. Install virtualenv-burrito: https://github.com/brainsik/virtualenv-burrito

6. Create and use virtualenv for paegan
    $ mkvirtualenv paegan
    $ workon paegan

7. Install paegan library dependencies
    $ pip install paegan

8. Run the paegan tests
    $ git clone git@github.com:asascience-open/paegan.git
    $ cd paegan
    $ pip install pytest
    $ python runtests.py


Contributors
============
Kyle Wilcox <kwilcox@asascience.com>
Alex Crosby <acrosby@asascience.com>
