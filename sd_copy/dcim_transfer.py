import json
import logging
import os.path
import shlex
import subprocess
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from enum import Enum
from operator import attrgetter
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union

from sd_copy.cameras import Camera, dji_osmo_action_photo_camera, dji_osmo_action_video_camera, fujifilm_x_t3
from sd_copy.utils import UnexpectedDataError, get_datetime_from_str, get_single_value


class Extension(Enum):
    jpg = ".jpg"
    mov = ".mov"
    mp4 = ".mp4"
    raf = ".raf"
    aac = ".aac"


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


def get_camera(exif_data: dict) -> Camera:
    camera_identifier = exif_data.get("EXIF:Model") or exif_data.get("QuickTime:HandlerDescription")
    if not camera_identifier:
        raise UnexpectedDataError("EXIF data does not match X-T3 or Osmo Action known outputs")
    return {
        "X-T3": fujifilm_x_t3,
        "\u0010DJI.Meta": dji_osmo_action_video_camera,  # used in case of videos
        "DJI Osmo Action": dji_osmo_action_photo_camera,  # used in case of images
    }[camera_identifier]


def get_matching_video_file_path(media_file) -> Path:
    # On DJI Osmo Action, separate AAC audio files are recorded alongside slow motion video. The same file name is
    # used; for example DJI_0375.AAC and DJI_0375.MOV. Since the audio files do not have Exif metadata, use instead
    # the corresponding video file to provide surrogate Exif metadata.
    (matching_video_file,) = filter(
        os.path.exists,
        tuple(str(media_file).replace(".AAC", suffix) for suffix in (".MOV", ".MP4")),
    )
    return Path(matching_video_file)


def get_metadata_from_exiftool(media_file: Path) -> dict:
    return get_single_value(
        json.loads(
            subprocess.run(
                shlex.split(f"exiftool -j -G '{media_file}'"),
                capture_output=True,
                check=True,
                text=True,
            ).stdout,
        ),
    )


def get_metadata(media_file: Path) -> dict:
    return get_metadata_from_exiftool(
        media_file=media_file if not media_file.suffix == ".AAC" else get_matching_video_file_path(media_file),
    )


def get_sanitized_file_name(path: Path) -> str:
    return path.stem.replace("_", "", 1).replace("_", "-")


def get_image_or_video(media_file: Path) -> Union[Image, Video]:
    exif_data = get_metadata(media_file=media_file)

    base_medium = BaseMedium(
        file_modify_date=datetime.strptime(exif_data["File:FileModifyDate"], "%Y:%m:%d %H:%M:%S%z"),
        camera=get_camera(exif_data),
        file_name=get_sanitized_file_name(path=media_file),
        extension=Extension(media_file.suffix.lower()),
        mime_type=exif_data["File:MIMEType"],
    )

    if base_medium.mime_type in ("video/quicktime", "video/mp4"):
        metadata = Video(
            **base_medium.asdict_shallow(),
            exif_date=get_datetime_from_str(exif_data[base_medium.camera.exif_date_field]),
            resolution=f"{exif_data['QuickTime:ImageHeight']}p",
            fps=f"{round(exif_data['QuickTime:VideoFrameRate'], 2)}fps",
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


def get_rectified_modify_date(metadata: Union[Image, Video], time_offset: int) -> datetime:
    return metadata.exif_date + metadata.camera.exif_date_timedelta + timedelta(seconds=time_offset)


def get_timestamp_str(date: datetime, metadata: Union[Image, Video], timelapse: bool) -> str:
    return datetime.strftime(
        date,
        f"%Y%m%d-%H%M{'%S' if timelapse and metadata.mime_type in ('image/jpeg', 'image/x-fujifilm-raf') else ''}",
    )


def get_target_path(
    destination: Path,
    metadata: Union[Image, Video],
    rectified_date: datetime,
    timelapse: bool,
    timelapse_n: Optional[int] = None,
) -> Path:
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
                    get_timestamp_str(date=rectified_date, metadata=metadata, timelapse=timelapse),
                    metadata.camera.name,
                    metadata.file_name if not timelapse_n else f"{metadata.file_name}-{timelapse_n:04d}",
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


def get_dcim_transfer_object(
    media_file: Path,
    destination: Path,
    time_offset: int,
    timelapse: bool,
) -> DCIMTransfer:
    logging.info(f"Getting DCIM object for {media_file}")
    metadata = get_image_or_video(media_file=media_file)
    rectified_modify_date = get_rectified_modify_date(metadata=metadata, time_offset=time_offset)
    return DCIMTransfer(
        source_path=media_file,
        metadata=metadata,
        rectified_modify_date=rectified_modify_date,
        target_path=get_target_path(
            destination=destination,
            metadata=metadata,
            rectified_date=rectified_modify_date,
            timelapse=timelapse,
        ),
    )


def is_media_file(file: Path) -> bool:
    if file.stem.startswith("._"):
        logging.warning(f"Found non-media file {file.name}, skipping.")
        return False
    return True


def get_dcim_transfers(
    source_path: Path,
    destination_path: Path,
    time_offset: int,
    timelapse: bool,
) -> Sequence[DCIMTransfer]:
    return tuple(
        get_dcim_transfer_object(
            media_file=file,
            destination=destination_path,
            time_offset=time_offset,
            timelapse=timelapse,
        )
        for file in source_path.rglob("*")
        if is_media_file(file)
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


def write_json_to_file(dcim_transfers: Sequence[DCIMTransfer], file_name: str):
    Path(f"{file_name}.json").write_text(
        json.dumps(
            tuple(
                {
                    "file": str(dcim_transfer.source_path),
                    "rectified_timestamp": str(dcim_transfer.rectified_modify_date),
                }
                for dcim_transfer in dcim_transfers
            ),
            indent=2,
        ),
    )


def assert_target_sorting_matches_source(dcim_transfers: Sequence[DCIMTransfer], exclude: Optional[Extension]):
    sorted_by_source = get_sorted_transfers(dcim_transfers, sort_key=attrgetter("source_path"), exclude=exclude)
    sorted_by_target = get_sorted_transfers(dcim_transfers, sort_key=attrgetter("target_path"), exclude=exclude)

    if sorted_by_source != sorted_by_target:
        write_json_to_file(sorted_by_target, "sorted_by_target")
        write_json_to_file(sorted_by_source, "sorted_by_source")
        raise AssertionError
