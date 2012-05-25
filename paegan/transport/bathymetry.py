class Bathymetry():
    def __init__(self, **kwargs):
        True

    def intersect(self, **kwargs):
        """
            Intersect a Line or Point Collection and the Bathymetry
        """
        ls = None
        if "linestring" in kwargs:
            ls = kwargs.pop('linestring')
        elif "start_point" and "end_point" in kwargs:
            ls = LineString(list(kwargs.pop('start_point').coords) + list(kwargs.pop('end_point').coords))
        else:
            raise TypeError( "must provide a LineString geometry object or (2) Point geometry objects" )

        inter = False
        return inter