import os
import unittest
from urlparse import urlparse
from paegan.utils.asarandom import AsaRandom

class AsaRandomTest(unittest.TestCase):
    def test_create_random_filename(self):
        temp_filename = AsaRandom.filename(prefix="superduper", suffix=".nc")

        path = urlparse(temp_filename).path
        name, ext = os.path.splitext(path)

        assert name.index("superduper") == 0
        assert ext == ".nc"