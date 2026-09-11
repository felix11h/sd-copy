from dataclasses import dataclass
from datetime import timedelta
from typing import Optional


@dataclass
class Camera:
    name: str
    # EXIF metadata field to use for computing rectified timestamp. Set to `None` for cameras
    # where the timestamp should be parsed from file name
    exif_date_field: Optional[str]
    # Timedelta that needs to be applied to timestamp from exif_date_field
    exif_date_timedelta: timedelta
    # Format used for parsing timestamp from the original file name, if `exif_date_field` is `None`
    filename_date_format: Optional[str] = None


# TODO: Parse this from yaml in the future
fujifilm_x_t3 = Camera(
    name="x-t3",
    exif_date_field="EXIF:DateTimeOriginal",
    exif_date_timedelta=timedelta(hours=0),
)

dji_osmo_action_video_camera = Camera(
    name="dji-oa",
    exif_date_field="QuickTime:MediaCreateDate",
    exif_date_timedelta=timedelta(hours=1),
)

dji_osmo_action_photo_camera = Camera(
    name="dji-oa",
    exif_date_field="EXIF:DateTimeOriginal",
    exif_date_timedelta=timedelta(hours=0),
)

obs = Camera(
    name="obs",
    exif_date_field=None,
    exif_date_timedelta=timedelta(hours=0),
    filename_date_format="%Y-%m-%d_%H-%M-%S",
)
