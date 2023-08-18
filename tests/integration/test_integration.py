import json
import os
import subprocess
from distutils.dir_util import copy_tree
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from sd_copy.dcim_transfer import Image, Video, get_dcim_transfers, get_image_or_video

DATA = "dcim"
FUJIFILM_DCIM = os.path.join(DATA, "100_Fuji")
DJI_OA_DCIM = os.path.join(DATA, "100MEDIA")


def _run_process(command: str):
    subprocess.run(command, check=True, shell=True)


def _folder_empty(path: str) -> bool:
    if os.path.exists(path) and os.path.isdir(path):
        return not os.listdir(path)
    else:
        raise Exception(f"Directory {path} does not exist")


def _number_of_files(path: str) -> int:
    return len(os.listdir(path))


class TestSdCopy(TestCase):
    def setUp(self):
        """Called for every test method. If this gets too much, use classmethod setUpClass instead."""

        if _folder_empty(path=DATA):
            raise Exception(f"Missing test data in {DATA}. Did you forget to update the submodule (see README)?")

        self.fuji_dcim_location = TemporaryDirectory()
        copy_tree(src=FUJIFILM_DCIM, dst=self.fuji_dcim_location.name)
        self.dji_oa_dcim_location = TemporaryDirectory()
        copy_tree(src=DJI_OA_DCIM, dst=self.dji_oa_dcim_location.name)

        self.output_location = TemporaryDirectory()

    def tearDown(self):
        # Make clean up explicit, even though it would be done without these commands
        self.fuji_dcim_location.cleanup()
        self.dji_oa_dcim_location.cleanup()
        self.output_location.cleanup()

    def test_running_sd_copy_with_dry_run_does_not_copy_files(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        _run_process(f"sd-copy {self.fuji_dcim_location.name} {self.output_location.name} --dry-run")
        self.assertTrue(_folder_empty(path=self.output_location.name))

    def test_running_sd_copy_on_fujifilm_test_files_copies_expected_files(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        _run_process(f"sd-copy {self.fuji_dcim_location.name} {self.output_location.name}")
        self.assertEqual(
            _number_of_files(os.path.join(self.output_location.name, "2021-07-08")),
            _number_of_files(self.fuji_dcim_location.name),
        )

    def test_runnning_sd_copy_on_dji_test_files_copies_expected_files(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        _run_process(f"sd-copy {self.dji_oa_dcim_location.name} {self.output_location.name}")
        hidden_files = ("._DJI_0373.MOV",)
        self.assertEqual(
            _number_of_files(os.path.join(self.output_location.name, "2021-09-14")),
            _number_of_files(self.dji_oa_dcim_location.name) - len(hidden_files),
        )

    def test_sd_copy_handles_existing_output_locations_correctly(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        output_location_subfolder = os.path.join(self.output_location.name, "2021-09-14")
        os.mkdir(output_location_subfolder)
        self.assertTrue(_folder_empty(output_location_subfolder))
        _run_process(f"sd-copy {self.dji_oa_dcim_location.name} {self.output_location.name}")
        self.assertFalse(_folder_empty(output_location_subfolder))


class TestGetImageOrVideo(TestCase):
    def test_fujifilm_get_image_or_video(self):
        fujifilm_dcim_path = Path(FUJIFILM_DCIM)
        self.assertIsInstance(get_image_or_video(fujifilm_dcim_path / "DSCF0226.JPG"), Image)
        self.assertIsInstance(get_image_or_video(fujifilm_dcim_path / "DSCF0226.JPG"), Image)
        self.assertIsInstance(get_image_or_video(fujifilm_dcim_path / "DSCF0231.RAF"), Image)
        self.assertIsInstance(get_image_or_video(fujifilm_dcim_path / "DSCF0229.MOV"), Video)

    def test_dji_oa_get_image_or_video(self):
        dji_oa_dcim_path = Path(DJI_OA_DCIM)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0373.MOV"), Video)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0375.MOV"), Video)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0375.AAC"), Video)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0376.JPG"), Image)
        self.assertIsInstance(get_image_or_video(dji_oa_dcim_path / "DJI_0377.MP4"), Video)
