from datetime import datetime
from unittest import TestCase

from sd_copy.utils import get_datetime_from_str


class GetDatetimeFromString(TestCase):
    def test_get_datetime_from_str(self):
        self.assertEqual(
            get_datetime_from_str(timestamp="2020:06:28 10:06:34"),
            datetime(year=2020, month=6, day=28, hour=10, minute=6, second=34),
        )

    def test_timezone_raises_error(self):
        self.assertRaises(ValueError, get_datetime_from_str, "2020:06:28 10:06:34+02:00")

    def test_unmatched_format_raises_error(self):
        self.assertRaises(ValueError, get_datetime_from_str, "2020-06-28 10:06:34+02:00")
