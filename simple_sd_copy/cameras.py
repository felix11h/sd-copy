from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Camera:
    name: str
    exif_date_field: str  # name of the Exif create or modify field to use as basis for the rectified timestamp
    exif_date_timedelta: timedelta  # timedelta that needs to be applied to timestamp from exif_date_field


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
