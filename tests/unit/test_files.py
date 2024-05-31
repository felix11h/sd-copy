from pathlib import Path
from unittest import TestCase

from sd_copy.files import get_files_not_sorted


class TestGetFilesNotSorted(TestCase):
    def test_sorted_files_are_identified_correctly(self):
        self.assertEqual(
            get_files_not_sorted(
                files_to_check=(Path("DSCF0226.JPG"),),
                sorted_files=(Path("20220101-1200_x-t3_DSCF0226_attributes.jpg"),),
            ),
            (),
        )

    def test_unsorted_files_are_returned(self):
        self.assertEqual(
            get_files_not_sorted(
                files_to_check=(Path("DSCF0226.JPG"),),
                sorted_files=(Path("20220101-1200_x-t3_DSCF1000_attributes.jpg"),),
            ),
            ("DSCF0226.JPG",),
        )
