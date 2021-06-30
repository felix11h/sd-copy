
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Sequence

import click
from exiftool import ExifTool


class Camera(Enum):
    xt3 = "x-t3"


class Extension(Enum):
    jpg = ".jpg"
    mov = ".mov"


@dataclass
class Media:
    modify_date: datetime
    camera: Camera
    file_name: str
    extension: Extension


@dataclass
class Image:
    aperture: float
    focal_length: int


@dataclass
class Video:
    resolution: str
    fps: str


def get_target_path(source_path: Path, target_folder: Path) -> Path:

    with ExifTool() as exif_tool:
        exif_data = exif_tool.get_metadata(str(source_path))

    media = Media(
        modify_date=datetime.strptime(exif_data["File:FileModifyDate"], "%Y:%m:%d %H:%M:%S%z"),
        camera=Camera.xt3,
        file_name=source_path.stem,
        extension=Extension(source_path.suffix.lower())
    )

    def get_video_file_name_additions() -> Sequence[str]:
        video = Video(
            resolution=f"{exif_data['QuickTime:ImageHeight']}p",
            fps=f"{exif_data['QuickTime:VideoFrameRate']}fps",
        )
        return (
            f"{video.resolution}-{video.fps}",
        )

    def get_image_file_name_additions() -> Sequence[str]:
        image = Image(
            aperture=exif_data["EXIF:ApertureValue"],
            focal_length=exif_data["EXIF:FocalLength"],
        )
        return (
            f"{image.aperture}-{image.focal_length}",
        )

    return target_folder / datetime.strftime(media.modify_date, '%Y-%m-%d') / Path(
        "_".join(
            (
                datetime.strftime(media.modify_date, '%Y%m%d-%H%M%S'),
                media.camera.value,
                media.file_name,
                *(
                    {
                        "image/jpeg": get_image_file_name_additions,
                        "video/quicktime": get_video_file_name_additions,
                    }[exif_data["File:MIMEType"]]()
                ),
            ),
        ) + media.extension.value,
    )


@click.command()
@click.argument('src', type=click.Path(exists=True, path_type=Path))
@click.argument('dst', type=click.Path(exists=True, path_type=Path))
@click.option('--dry-run', '-n', default=False, is_flag=True)
def main(src: Path, dst: Path, dry_run: bool):
    print(type(src))
    print(dry_run)





# print(get_target_path(source_path=Path("data/DSCF0023.MOV"), target_folder=Path("hello/")))
# print(get_target_path(source_path=Path("data/DSCF0021.JPG"), target_folder=Path("world/")))

if __name__ == "__main__":
    main()
