from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from sd_copy.cameras import dji_osmo_action_photo_camera, dji_osmo_action_video_camera, fujifilm_x_t3
from sd_copy.dcim_transfer import get_camera, get_metadata, get_sanitized_file_name, is_media_file
from sd_copy.utils import UnexpectedDataError


class TestGetCamera(TestCase):
    def test_get_camera_raises_error_when_no_identifier(self):
        self.assertRaises(UnexpectedDataError, get_camera, {})

    def test_get_camera_fujifilm_x_t3(self):
        self.assertEqual(get_camera({"EXIF:Model": "X-T3"}), fujifilm_x_t3)

    def test_get_camera_dji_osmo_action_video_camera(self):
        self.assertEqual(get_camera({"QuickTime:HandlerDescription": "\u0010DJI.Meta"}), dji_osmo_action_video_camera)

    def test_get_camera_dji_osmo_action_photo_camera(self):
        self.assertEqual(get_camera({"QuickTime:HandlerDescription": "DJI Osmo Action"}), dji_osmo_action_photo_camera)


class TestIsMediaFile(TestCase):
    def test_is_media_file_returns_false_for_dji_hidden_files(self):
        self.assertFalse(is_media_file(Path("dcim/100MEDIA/._DJI_0373.MOV")))


class TestGetSanitizedFileName(TestCase):
    def test_get_sanitized_file_name_for_known_cases(self):
        self.assertEqual("DJI0375", get_sanitized_file_name(Path("dcim/100MEDIA/DJI_0375.MOV")))
        self.assertEqual("DJI0013-001", get_sanitized_file_name(Path("dcim/100MEDIA/DJI_0013_001.MP4")))


class TestGetMetadata(TestCase):
    @patch("sd_copy.dcim_transfer.get_matching_video_file_path")
    @patch("sd_copy.dcim_transfer.get_metadata_from_exiftool")
    def test_get_metadata_makes_expected_calls_for_aac_file(
        self,
        mock_get_metdata_from_exiftool,
        mock_get_matching_video_file_path,
    ):
        test_path = Path("test/path.AAC")
        _ = get_metadata(test_path)
        mock_get_matching_video_file_path.assert_called_once_with(test_path)
        mock_get_metdata_from_exiftool.assert_called_with(media_file=mock_get_matching_video_file_path.return_value)

    @patch("sd_copy.dcim_transfer.get_matching_video_file_path")
    @patch("sd_copy.dcim_transfer.get_metadata_from_exiftool")
    def test_get_metadata_makes_expected_calls_for_video_file(
        self,
        mock_get_metadata_from_exiftool,
        mock_get_matching_video_file_path,
    ):
        test_path = Path("test/path.MOV")
        _ = get_metadata(Path(test_path))
        mock_get_matching_video_file_path.assert_not_called()
        mock_get_metadata_from_exiftool.assert_called_with(media_file=test_path)

    pass
