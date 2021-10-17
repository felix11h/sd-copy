import os
import subprocess
from distutils.dir_util import copy_tree
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from simple_sd_copy.dcim_transfer import Image, Video, get_image_or_video

DATA = "dcim"
FUJIFILM_DCIM = os.path.join(DATA, "100_Fuji")
DJI_OA_DCIM = os.path.join(DATA, "100MEDIA")


def _folder_empty(path: str) -> bool:
    if os.path.exists(path) and os.path.isdir(path):
        return not os.listdir(path)
    else:
        raise Exception(f"Directory {path} does not exist")


class TestSimpleSdCopy(TestCase):
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

    def test_simple_sd_copy_dry_run(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))
        _ = subprocess.check_output(
            ["simple-sd-copy", self.fuji_dcim_location.name, self.output_location.name, "--dry-run"],
        )
        self.assertTrue(_folder_empty(path=self.output_location.name))

    def test_simple_sd_copy_multiple_formats(self):
        self.assertTrue(_folder_empty(path=self.output_location.name))

        _ = subprocess.check_output(["simple-sd-copy", self.fuji_dcim_location.name, self.output_location.name])
        os.mkdir(os.path.join(self.output_location.name, "2021-09-14"))  # existing folders should not cause a problems
        _ = subprocess.check_output(["simple-sd-copy", self.dji_oa_dcim_location.name, self.output_location.name])

        self.assertFalse(_folder_empty(path=os.path.join(self.output_location.name, "2021-07-08")))
        self.assertFalse(_folder_empty(path=os.path.join(self.output_location.name, "2021-09-14")))


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
