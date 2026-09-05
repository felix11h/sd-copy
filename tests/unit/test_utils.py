from datetime import datetime
from pathlib import Path
from unittest import TestCase

from sd_copy.utils import get_checksum, get_datetime_from_str, get_numeric_hash


class TestGetDatetimeFromString(TestCase):
    def test_get_datetime_from_str(self):
        self.assertEqual(
            get_datetime_from_str(timestamp="2020:06:28 10:06:34"),
            datetime(year=2020, month=6, day=28, hour=10, minute=6, second=34),
        )

    def test_timezone_raises_error(self):
        self.assertRaises(ValueError, get_datetime_from_str, "2020:06:28 10:06:34+02:00")

    def test_unmatched_format_raises_error(self):
        self.assertRaises(ValueError, get_datetime_from_str, "2020-06-28 10:06:34+02:00")


class TestGetChecksum(TestCase):
    def test_get_checksum_for_file(self):
        self.assertEqual("e4026615df7cc162b7e53eefdab78328", get_checksum(file=Path("dcim/100MEDIA/DJI_0373.MOV")))


class TestGetNumericHash(TestCase):
    def test_get_numeric_hash_for_file(self):
        self.assertEqual("7928", get_numeric_hash(file=Path("dcim/OBS/2026-09-05_11-36-47.mkv")))

    def test_get_numeric_hash_is_stable_and_zero_padded(self):
        self.assertEqual(
            get_numeric_hash(Path("dcim/OBS/2026-09-05_11-36-47.mkv")),
            get_numeric_hash(Path("dcim/OBS/2026-09-05_11-36-47.mkv")),
        )
        self.assertEqual(4, len(get_numeric_hash(Path("dcim/OBS/2026-09-05_11-36-47.mkv"))))
