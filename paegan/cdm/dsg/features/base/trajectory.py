from paegan.cdm.dsg.collections.base.point_collection import PointCollection

class Trajectory(PointCollection):
    """
        A collection of Points along a 1 dimensional path, connected in space and time.
        The Points are ordered in time (in other words, the time dimension must
        increase monotonically along the trajectory).
    """

    def __init__(self, **kwargs):
        super(Trajectory,self).__init__(**kwargs)
        self._type = "Trajectory"

    def get_path(self):
        """
            Returns the Points along the trajectory
        """
        return map(lambda x: [x.location, x.time], self._elements)