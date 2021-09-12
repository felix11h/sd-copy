from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
from operator import attrgetter
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union

from exiftool import ExifTool

from simple_sd_copy.cameras import Camera, dji_osmo_action, fujifilm_x_t3
from simple_sd_copy.utils import UnexpectedDataError, get_datetime_from_str


class Extension(Enum):
    jpg = ".jpg"
    mov = ".mov"
    mp4 = ".mp4"
    raf = ".raf"


@dataclass
class BaseMedium:
    file_modify_date: datetime
    camera: Camera
    file_name: str
    extension: Extension
    mime_type: str

    def asdict_shallow(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass
class Image(BaseMedium):
    exif_date: datetime
    resolution: str


@dataclass
class Video(BaseMedium):
    exif_date: datetime
    resolution: str
    fps: str


@dataclass
class DCIMTransfer:
    source_path: Path
    metadata: Union[Image, Video]
    rectified_modify_date: datetime
    target_path: Path


def get_camera_from_exif_data(exif_data: dict) -> Camera:
    camera_identifier = exif_data.get("EXIF:Model") or exif_data.get("QuickTime:HandlerDescription")
    if not camera_identifier:
        raise UnexpectedDataError("EXIF data does not match X-T3 or Osmo Action known outputs")
    return {
        "X-T3": fujifilm_x_t3,
        "\u0010DJI.Meta": dji_osmo_action,
    }[camera_identifier]


def get_image_or_video(media_file: Path) -> Union[Image, Video]:

    with ExifTool() as exif_tool:
        exif_data = exif_tool.get_metadata(str(media_file))

    base_medium = BaseMedium(
        file_modify_date=datetime.strptime(exif_data["File:FileModifyDate"], "%Y:%m:%d %H:%M:%S%z"),
        camera=get_camera_from_exif_data(exif_data),
        file_name=media_file.stem.replace("_", ""),
        extension=Extension(media_file.suffix.lower()),
        mime_type=exif_data["File:MIMEType"],
    )

    if base_medium.mime_type in ("video/quicktime", "video/mp4"):
        metadata = Video(
            **base_medium.asdict_shallow(),
            exif_date=get_datetime_from_str(exif_data[base_medium.camera.exif_date_field]),
            resolution=f"{exif_data['QuickTime:ImageHeight']}p",
            fps=f"{round(exif_data['QuickTime:VideoFrameRate'],2)}fps",
        )
    elif base_medium.mime_type in ("image/jpeg", "image/x-fujifilm-raf"):
        metadata = Image(
            **base_medium.asdict_shallow(),
            exif_date=get_datetime_from_str(exif_data[base_medium.camera.exif_date_field]),
            resolution=f"{exif_data['EXIF:ExifImageWidth']}x{exif_data['EXIF:ExifImageHeight']}",
        )
    else:
        raise UnexpectedDataError(
            f"'{base_medium.mime_type}' MIMEType of {media_file.name} not yet handled",
        )

    return metadata


def get_rectified_modify_date(metadata: Union[Image, Video]) -> datetime:
    return metadata.exif_date + metadata.camera.exif_date_timedelta


def get_target_path(destination: Path, metadata: Union[Image, Video], rectified_date: datetime) -> Path:
    def get_video_file_name_additions(video: Video) -> Sequence[str]:
        return (f"{video.resolution}-{video.fps}",)

    def get_image_file_name_additions(image: Image) -> Sequence[str]:
        return (image.resolution,)

    return (
        destination
        / datetime.strftime(rectified_date, "%Y-%m-%d")
        / Path(
            "_".join(
                (
                    datetime.strftime(rectified_date, "%Y%m%d-%H%M"),
                    metadata.camera.name,
                    metadata.file_name,
                    *(
                        {
                            "image/jpeg": get_image_file_name_additions,
                            "image/x-fujifilm-raf": get_image_file_name_additions,
                            "video/quicktime": get_video_file_name_additions,
                            "video/mp4": get_video_file_name_additions,
                        }[metadata.mime_type](metadata)
                    ),
                ),
            )
            + metadata.extension.value,
        )
    )


def get_dcim_transfer_object(media_file: Path, destination: Path) -> DCIMTransfer:
    metadata = get_image_or_video(media_file=media_file)
    rectified_modify_date = get_rectified_modify_date(metadata=metadata)
    return DCIMTransfer(
        source_path=media_file,
        metadata=metadata,
        rectified_modify_date=rectified_modify_date,
        target_path=get_target_path(destination=destination, metadata=metadata, rectified_date=rectified_modify_date),
    )


def get_dcim_transfers(source_path: Path, destination_path: Path) -> Sequence[DCIMTransfer]:
    return tuple(
        get_dcim_transfer_object(media_file=media_file, destination=destination_path)
        for media_file in source_path.rglob("*")
    )


def get_sorted_transfers(
    dcim_transfers: Sequence[DCIMTransfer],
    sort_key: Callable,
    exclude: Optional[Extension] = None,
) -> Sequence[DCIMTransfer]:
    return tuple(
        sorted(
            filter(lambda obj: obj.metadata.extension != exclude, dcim_transfers) if exclude else dcim_transfers,
            key=sort_key,
        ),
    )


def assert_target_sorting_matches_source(dcim_transfers: Sequence[DCIMTransfer], exclude: Optional[Extension]):
    sorted_by_source = get_sorted_transfers(dcim_transfers, sort_key=attrgetter("source_path"), exclude=exclude)
    sorted_by_target = get_sorted_transfers(dcim_transfers, sort_key=attrgetter("target_path"), exclude=exclude)
    assert sorted_by_source == sorted_by_target
