from shapely.geometry import MultiPoint

from paegan.cdm.dsg.collections.base.profile_collection import ProfileCollection
from paegan.utils.asalist import AsaList

class StationProfile(ProfileCollection):
    """
    A collection of Profiles at a single location.

    This mimics the Station class API, they should likely be merged somehow.
    """
    def __init__(self, **kwargs):
        super(StationProfile, self).__init__(**kwargs)

        self._type       = "timeSeriesProfile"
        self._properties = {}
        self._location   = None
        self.uid         = None
        self.name        = None
        self.description = None

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value

        # Sets the location of every Profile in this station if it is not already set
        for profile in self._elements:
            if profile.location is None:
                profile.location == value

    def get_properties(self):
        return self._properties

    def get_property(self, prop):
        return self._properties.get(prop, None)

    def set_property(self, prop, value):
        self._properties[prop] = value

    def get_unique_members(self):
        all_members = [pt.members for prof in self._elements
                                  for pt in prof._elements]

        keys = ["name", "description", "standard", "units"]
        mwhat = []
        for mg in all_members:
            for m in mg:
                mwhat.append( { key: m[key] for key in keys if key in m } )

        # Now unique them on name
        mwhat = { x['name']:x for x in mwhat }.values()

        return mwhat

    def calculate_bounds(self):
        """
            Calculate the time_range, depth_range, bbox, and size of this collection.
            Will scan all data.
            Ensures that .size, .bbox and .time_range return non-null.

            If the collection already knows its bbox; time_range; and/or size,
            they are recomputed.
        """
        # tell all contained profiles to calculate their bounds
        map(lambda x: x.calculate_bounds(), self._elements)

        # @TODO size is just number of timesteps?
        self.size = len(self._elements)

        # bbox is just this point
        self.bbox = MultiPoint([self.location, self.location]).envelope

        time_set = set()
        map(time_set.add, AsaList.flatten([p.time for p in self._elements]))
        self.time_range = sorted(list(time_set))

        depth_set = set()
        map(depth_set.add, AsaList.flatten([p.depth_range for p in self._elements]))
        self.depth_range = sorted(list(depth_set))



