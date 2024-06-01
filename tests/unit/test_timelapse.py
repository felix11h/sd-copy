from functools import partial
from unittest import TestCase
from unittest.mock import Mock

from sd_copy.timelapse import TimelapseSpec, get_timelapse_duration_from_spec


class TestTimelapseDuration(TestCase):
    def test_correct_timelapse_duration(self):
        make_spec = partial(
            TimelapseSpec,
            timestamp=Mock(),
            camera=Mock(),
            first_image_name=Mock(),
            last_image_name=Mock(),
            shutter_speed=Mock(),
        )

        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=2, dt=60)), "1m")
        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=2, dt=600)), "10m")
        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=61, dt=1)), "1m")
        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=541, dt=1)), "9m")
        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=541, dt=3)), "27m")
        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=361, dt=10)), "1h00m")
        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=368, dt=10)), "1h01m")
        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=360, dt=10)), "59m")
        self.assertEqual(get_timelapse_duration_from_spec(make_spec(n_images=200, dt=600)), "33h10m")
