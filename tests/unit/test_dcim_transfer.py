from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from simple_sd_copy.cameras import dji_osmo_action_photo_camera, dji_osmo_action_video_camera, fujifilm_x_t3
from simple_sd_copy.dcim_transfer import get_camera, get_metadata
from simple_sd_copy.utils import UnexpectedDataError


class TestGetCamera(TestCase):
    def test_get_camera_raises_error_when_no_identifier(self):
        self.assertRaises(UnexpectedDataError, get_camera, {})

    def test_get_camera_fujifilm_x_t3(self):
        self.assertEqual(get_camera({"EXIF:Model": "X-T3"}), fujifilm_x_t3)

    def test_get_camera_dji_osmo_action_video_camera(self):
        self.assertEqual(get_camera({"QuickTime:HandlerDescription": "\u0010DJI.Meta"}), dji_osmo_action_video_camera)

    def test_get_camera_dji_osmo_action_photo_camera(self):
        self.assertEqual(get_camera({"QuickTime:HandlerDescription": "DJI Osmo Action"}), dji_osmo_action_photo_camera)


class TestGetMetadata(TestCase):
    @patch("simple_sd_copy.dcim_transfer.ExifTool")
    def test_get_metadata_for_aac_file(self, mock_exiftool):
        _ = get_metadata(Path("path.AAC"))
        mock_exiftool.return_value.__enter__.return_value.get_metadata.assert_called_with(filename="path.MOV")

    @patch("simple_sd_copy.dcim_transfer.ExifTool")
    def test_get_metadata_for_non_aac_files(self, mock_exiftool):
        path_str = "path.MOV"
        _ = get_metadata(Path(path_str))
        mock_exiftool.return_value.__enter__.return_value.get_metadata.assert_called_with(filename=path_str)
