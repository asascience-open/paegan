import os
from osgeo import ogr
from shapely import wkb, geometry
from shapely.geometry import LineString

class Shoreline(object):
    def __init__(self, **kwargs):
        """
            Optional named arguments: 
            * file (local path to OGC complient file)
        """

        if "file" in kwargs:
            self._file = os.path.normpath(kwargs.pop('file'))
        else:
            self._file = os.path.normpath(os.path.join(__file__,"../../resources/shoreline/global/10m_land.shp"))

        source = ogr.Open(self._file)
        if not source:
            raise Exception('Could not load {}'.format(self._file))

        layer = source.GetLayer()
        self._geoms = []
        for element in layer:
            self._geoms.append(wkb.loads(element.GetGeometryRef().ExportToWkb()))

    def intersect(self, **kwargs):
        """
            Intersect a Line or Point Collection and the Shoreline
        """
        ls = None
        if "linestring" in kwargs:
            ls = kwargs.pop('linestring')
        elif "start_point" and "end_point" in kwargs:
            ls = LineString(list(kwargs.pop('start_point').coords) + list(kwargs.pop('end_point').coords))
        else:
            raise TypeError( "must provide a LineString geometry object or (2) Point geometry objects" )

        inter = False
        for element in self._geoms:
            inter = ls.intersection(element)
            if inter:
                break

        return inter