from pathlib import Path
from unittest import TestCase

from sd_copy.files import get_files_not_sorted, get_renamed_folder_path


class TestGetRenamedFolderPath(TestCase):
    def test_return_none_for_unchanged_folder(self):
        self.assertEqual(
            get_renamed_folder_path(
                old_folder_path=Path("/synced/library/2024-05-31 name pt. 1"),
                source_folders=(Path("/origin/library/2024-05-31 name pt. 1"),),
            ),
            None,
        )

    def test_return_new_path_for_updated_folder(self):
        self.assertEqual(
            get_renamed_folder_path(
                old_folder_path=Path("/synced/library/2024-05-31 previous name pt. 1"),
                source_folders=(Path("/origin/library/2024-05-31 updated name pt. 2"),),
            ),
            Path("/synced/library/2024-05-31 updated name pt. 2"),
        )

    def test_return_none_for_deleted_folder(self):
        self.assertEqual(
            get_renamed_folder_path(
                old_folder_path=Path("/synced/library/2024-05-31 previous name"),
                source_folders=(),
            ),
            None,
        )


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
