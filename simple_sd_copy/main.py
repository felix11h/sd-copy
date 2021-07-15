import os
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Sequence, Union

import click
from exiftool import ExifTool


class UnexpectedDataError(ValueError):
    """Raise when input data presents a case not yet handled."""


class MissingDependencyError(RuntimeError):
    """Raise when depeendencies are missing"""


class Camera(Enum):
    xt3 = "x-t3"
    dji_osmo_action = "dji-oa"


class Extension(Enum):
    jpg = ".jpg"
    mov = ".mov"
    raf = ".raf"


@dataclass
class BaseMedium:
    file_modify_date: datetime
    camera: Camera
    file_name: str
    extension: Extension
    mime_type: str


@dataclass
class Image(BaseMedium):
    exif_create_date: datetime
    exif_modify_date: datetime
    resolution: str


@dataclass
class Video(BaseMedium):
    exif_create_date: datetime
    exif_modify_date: datetime
    resolution: str
    fps: str


def check_if_exiftool_installed():
    if not shutil.which("exiftool"):
        raise MissingDependencyError("Exiftool not found, please install")


def get_datetime_from_str(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")


def get_camera_from_exif_data(exif_data: dict) -> Camera:
    camera_identifier = exif_data.get("EXIF:Model") or exif_data.get("QuickTime:HandlerDescription")
    if not camera_identifier:
        raise UnexpectedDataError("EXIF data does not match X-T3 or Osmo Action known outputs")
    return {
        "X-T3": Camera.xt3,
        "\u0010DJI.Meta": Camera.dji_osmo_action,
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

    if base_medium.mime_type in ("video/quicktime",):
        metadata = Video(
            **asdict(base_medium),
            exif_modify_date=get_datetime_from_str(exif_data["QuickTime:CreateDate"]),
            exif_create_date=get_datetime_from_str(exif_data["QuickTime:ModifyDate"]),
            resolution=f"{exif_data['QuickTime:ImageHeight']}p",
            fps=f"{round(exif_data['QuickTime:VideoFrameRate'],2)}fps",
        )
    elif base_medium.mime_type in ("image/jpeg", "image/x-fujifilm-raf"):
        metadata = Image(
            **asdict(base_medium),
            exif_modify_date=get_datetime_from_str(exif_data["EXIF:CreateDate"]),
            exif_create_date=get_datetime_from_str(exif_data["EXIF:ModifyDate"]),
            resolution=f"{exif_data['EXIF:ExifImageWidth']}x{exif_data['EXIF:ExifImageHeight']}",
        )
    else:
        raise UnexpectedDataError(
            f"'{base_medium.mime_type}' MIMEType of {media_file.name} not yet handled",
        )

    return metadata


def get_rectified_modify_date(metadata: Union[Image, Video]) -> datetime:
    assert metadata.exif_modify_date == metadata.exif_create_date
    return {
        Camera.xt3: metadata.file_modify_date - timedelta(hours=1),
        Camera.dji_osmo_action: metadata.exif_modify_date + timedelta(hours=2)
    }[metadata.camera]


def get_target_path(destination: Path, metadata: Union[Image, Video], rectified_date: datetime) -> Path:

    def get_video_file_name_additions(video: Video) -> Sequence[str]:
        return (
            f"{video.resolution}-{video.fps}",
        )

    def get_image_file_name_additions(image: Image) -> Sequence[str]:
        return (
            image.resolution,
        )

    return destination / datetime.strftime(rectified_date, '%Y-%m-%d') / Path(
        "_".join(
            (
                datetime.strftime(rectified_date, '%Y%m%d-%H%M%S'),
                metadata.camera.value,
                metadata.file_name,
                *(
                    {
                        "image/jpeg": get_image_file_name_additions,
                        "image/x-fujifilm-raf": get_image_file_name_additions,
                        "video/quicktime": get_video_file_name_additions,
                    }[metadata.mime_type](metadata)
                ),
            ),
        ) + metadata.extension.value,
    )


def copy_media_to_target(source_path: Path, target_path: Path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src=source_path, dst=target_path)


def update_exif_data(file_path: Path, rectified_modify_date: datetime):
    pass


def update_file_modify_date(file_path: Path, rectified_modify_date: datetime):
    os.utime(path=file_path, times=(rectified_modify_date.timestamp(), rectified_modify_date.timestamp()))


def remove_source_file(source_path: Path):
    pass


@click.command()
@click.argument('src', type=click.Path(exists=True, path_type=Path))
@click.argument('dst', type=click.Path(exists=True, path_type=Path))
@click.option('--dry-run', '-n', default=False, is_flag=True)
@click.option('--keep', '-k', default=False, is_flag=True)
def main(src: Path, dst: Path, dry_run: bool, keep: bool):

    check_if_exiftool_installed()

    for media_file in src.rglob("*"):

        metadata = get_image_or_video(media_file=media_file)
        rectified_date = get_rectified_modify_date(metadata=metadata)

        target_path = get_target_path(destination=dst, metadata=metadata, rectified_date=rectified_date)

        if not dry_run:
            copy_media_to_target(source_path=media_file, target_path=target_path)
            update_exif_data(file_path=media_file, rectified_modify_date=rectified_date)
            update_file_modify_date(file_path=target_path, rectified_modify_date=rectified_date)
            if not keep:
                remove_source_file(source_path=media_file)

        else:
            print(f"{media_file} --> {target_path}")


if __name__ == "__main__":
    main()
