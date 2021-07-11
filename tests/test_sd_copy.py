from pathlib import Path
from unittest import TestCase
#
# from simple_sd_copy.main import get_target_path
#
# # global_path = Path("data/new/")
#
# # content of test_sample.py
from simple_sd_copy.main import get_image_or_video, Image, Video, get_rectified_modify_date, get_target_path


class TestMetadataContent(TestCase):

    def test_xfoo(self):
        self.assertTrue(bool)

    def test_media(self):
        self.assertTrue(bool)

class TestSdCopy(TestCase):

    DATA = Path("data/new")

    def test_get_image_or_video(self):
        print(get_image_or_video(self.DATA / "DSCF0226.JPG"))
        print(get_image_or_video(self.DATA/ "DJI_0163.MOV"))
        self.assertIsInstance(get_image_or_video(self.DATA / "DSCF0226.JPG"), Image)
        self.assertIsInstance(get_image_or_video(self.DATA / "DSCF0231.RAF"), Image)
        self.assertIsInstance(get_image_or_video(self.DATA / "DSCF0229.MOV"), Video)
        self.assertIsInstance(get_image_or_video(self.DATA / "DJI_0163.MOV"), Video)

    def test_get_rectified_modification_date(self):
        for media_file in  ("DSCF0226.JPG", "DSCF0231.RAF", "DSCF0229.MOV", "DJI_0163.MOV"):
            print(get_rectified_modify_date(get_image_or_video(self.DATA / media_file)))

    def test_get_target_path(self):
        for media_file in ("DSCF0226.JPG", "DSCF0231.RAF", "DSCF0229.MOV", "DJI_0163.MOV"):
            print(
                get_target_path(
                    destination=Path("mock/"),
                    metadata=get_image_or_video(self.DATA / media_file),
                    rectified_date=get_rectified_modify_date(get_image_or_video(self.DATA / media_file)),
                )
            )

    def test_media(self):
        self.assertTrue(bool)
