from pathlib import Path
from unittest import TestCase

from sd_copy.timelapse import get_image_number


class TestGetImageNumber(TestCase):
    def test_get_image_number_cases(self):
        self.assertEqual(get_image_number(Path("DSCF0226.JPG")), 226)
        self.assertEqual(get_image_number(Path("/some/path/2314/DSCF0226.JPG")), 226)
        self.assertEqual(get_image_number(Path("DSCF9226.JPG")), 9226)
        self.assertEqual(get_image_number(Path("DSCF0231.RAF")), 231)
