import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, auto
from operator import attrgetter
from pathlib import Path
from typing import Optional, Sequence

import click
from more_itertools import bucket

from sd_copy.cameras import Camera
from sd_copy.check import sort_dcim_transfers
from sd_copy.dcim_transfer import DCIMTransfer, Extension, Image, Video, get_timestamp_str
from sd_copy.utils import UnexpectedDataError, get_optional_single_value, get_single_value

TIMELAPSE_PROXY_SUFFIX = Extension.mp4
TIMELAPSE_PROXY_FPS = 24


@dataclass
class TimelapseSpec:
    timestamp: datetime
    camera: Camera
    first_image_name: str
    last_image_name: Optional[str]
    n_images: int
    dt: int
    shutter_speed: str


@dataclass
class TimelapseTransfer:
    jpg_files: Sequence[DCIMTransfer]
    raw_files: Sequence[DCIMTransfer]
    video_file: Optional[DCIMTransfer]


class TimelapseDCIMType(StrEnum):
    JPGImage = auto()
    RAWImage = auto()
    Video = auto()


def evaluate_timelapse_dcim_transfer_by_type(transfer: DCIMTransfer) -> TimelapseDCIMType:
    if isinstance(transfer.metadata, Video):
        return TimelapseDCIMType.Video
    elif isinstance(transfer.metadata, Image) and transfer.target_path.suffix in (Extension.jpg,):
        return TimelapseDCIMType.JPGImage
    elif isinstance(transfer.metadata, Image) and transfer.target_path.suffix in (Extension.raf, Extension.dng):
        return TimelapseDCIMType.RAWImage
    else:
        raise UnexpectedDataError(f"Could not determine timelapse media type for '{transfer.source_path}'")


def sort_transfers_by_source_path(dcim_transfers=Sequence[DCIMTransfer]) -> Sequence[DCIMTransfer]:
    return sort_dcim_transfers(dcim_transfers=dcim_transfers, sort_key=attrgetter("source_path"))


def get_timelapse_transfer_from_dcim_transfers(dcim_transfers: Sequence[DCIMTransfer]) -> TimelapseTransfer:
    partitioned_transfers = bucket(iterable=dcim_transfers, key=evaluate_timelapse_dcim_transfer_by_type)
    return TimelapseTransfer(
        jpg_files=sort_transfers_by_source_path(partitioned_transfers[TimelapseDCIMType.JPGImage]),
        raw_files=sort_transfers_by_source_path(partitioned_transfers[TimelapseDCIMType.RAWImage]),
        video_file=get_optional_single_value(tuple(partitioned_transfers[TimelapseDCIMType.Video])),
    )


def get_first_or_last_name_if_any(dcim_transfers: Sequence[DCIMTransfer], position: str) -> Sequence[DCIMTransfer]:
    return (dcim_transfers[0 if position == "first" else -1].metadata.file_name,) if dcim_transfers else ()


def get_first_or_last_name_from_timelapse_transfer(timelapse_transfer: TimelapseTransfer, position) -> str:
    return get_single_value(
        {
            *get_first_or_last_name_if_any(dcim_transfers=timelapse_transfer.jpg_files, position=position),
            *get_first_or_last_name_if_any(dcim_transfers=timelapse_transfer.raw_files, position=position),
        },
    )


def rounded_timedeltas_value(timedeltas: Sequence[float]) -> int:
    click.secho("[Note] ", fg="blue", nl=False)
    click.secho(f"Multiple dt found in timeline {set(timedeltas)}, using rounded value")
    return round(sum(timedeltas) / len(timedeltas))


def compute_timedelta(sorted_dcim_transfers: Sequence) -> int:
    timedeltas = tuple(
        (next_image.rectified_modify_date - image.rectified_modify_date).total_seconds()
        for next_image, image in zip(sorted_dcim_transfers[1:], sorted_dcim_transfers[:-1])
    )

    if (max(timedeltas) - min(timedeltas)) > 2:
        raise UnexpectedDataError(
            "Images interval unexpected, timelapse might need to be split up:"
            "\n\t".join(
                tuple(
                    f"{next_image.source_path.name} -> {image.source_path.name}: "
                    f"dt={(next_image.rectified_modify_date-image.rectified_modify_date).total_seconds()}s"
                    for next_image, image in zip(sorted_dcim_transfers[1:], sorted_dcim_transfers[:-1])
                ),
            ),
        )

    return (
        int(get_single_value(unique_timedeltas))
        if len(unique_timedeltas := set(timedeltas)) == 1
        else rounded_timedeltas_value(timedeltas)
    )


def get_timelapse_timestamp(timelapse_transfer: TimelapseTransfer) -> datetime:
    return (
        timelapse_transfer.jpg_files[0].rectified_modify_date
        if timelapse_transfer.jpg_files
        else timelapse_transfer.raw_files[0].rectified_modify_date
    )


def get_timelapse_camera(timelapse_transfer: TimelapseTransfer) -> Camera:
    return (
        timelapse_transfer.jpg_files[0].metadata.camera
        if timelapse_transfer.jpg_files
        else timelapse_transfer.raw_files[0].metadata.camera
    )


def get_timelapse_first_image_name(timelapse_transfer: TimelapseTransfer) -> str:
    # Use video name for DJI, as timelapse photos are generically named
    if timelapse_transfer.video_file:
        return timelapse_transfer.video_file.metadata.file_name

    return get_first_or_last_name_from_timelapse_transfer(timelapse_transfer=timelapse_transfer, position="first")


def get_timelapse_last_image_name(timelapse_transfer: TimelapseTransfer) -> Optional[str]:
    # Last name not needed for DJI
    if timelapse_transfer.video_file:
        return None

    return get_first_or_last_name_from_timelapse_transfer(timelapse_transfer=timelapse_transfer, position="last")


def get_timelapse_n_images(timelapse_transfer: TimelapseTransfer) -> int:
    return get_single_value(
        {
            *((n_jpg_files,) if (n_jpg_files := len(timelapse_transfer.jpg_files)) else ()),
            *((n_raw_files,) if (n_raw_files := len(timelapse_transfer.raw_files)) else ()),
        },
    )


def get_timelapse_dt(timelapse_transfer: TimelapseTransfer) -> int:
    timedeltas = (
        *((compute_timedelta(timelapse_transfer.jpg_files),) if timelapse_transfer.jpg_files else ()),
        *((compute_timedelta(timelapse_transfer.raw_files),) if timelapse_transfer.raw_files else ()),
    )
    return get_single_value(tuple(set(timedeltas)))


def get_timelapse_shutter_speed(timelapse_transfer: TimelapseTransfer) -> str:
    return get_single_value(
        {
            *tuple(transfer.metadata.shutter_speed for transfer in timelapse_transfer.jpg_files),
            *tuple(transfer.metadata.shutter_speed for transfer in timelapse_transfer.raw_files),
        },
    )


def get_timelapse_spec_from_timelapse_transfer(timelapse_transfer: TimelapseTransfer) -> TimelapseSpec:
    return TimelapseSpec(
        timestamp=get_timelapse_timestamp(timelapse_transfer=timelapse_transfer),
        camera=get_timelapse_camera(timelapse_transfer=timelapse_transfer),
        first_image_name=get_timelapse_first_image_name(timelapse_transfer=timelapse_transfer),
        last_image_name=get_timelapse_last_image_name(timelapse_transfer=timelapse_transfer),
        n_images=get_timelapse_n_images(timelapse_transfer=timelapse_transfer),
        dt=get_timelapse_dt(timelapse_transfer=timelapse_transfer),
        shutter_speed=get_timelapse_shutter_speed(timelapse_transfer=timelapse_transfer),
    )


def get_timelapse_duration_from_spec(timelapse_spec: TimelapseSpec) -> str:
    hours = ((timelapse_spec.n_images - 1) * timelapse_spec.dt) // 3600
    minutes = (((timelapse_spec.n_images - 1) * timelapse_spec.dt) // 60) % 60
    return f"{f'{hours}h' if hours else ''}{f'{minutes:02d}' if hours else f'{minutes}'}m"


def patch_dcim_transfer_target_path(dcim_transfer: DCIMTransfer, target: Path) -> DCIMTransfer:
    dcim_transfer.target_path = dcim_transfer.target_path.parent / target
    return dcim_transfer


def get_timelapse_filename(dcim_transfer: DCIMTransfer, timelapse_base_name: str, n: int):
    return f"{timelapse_base_name}_{n:04d}{dcim_transfer.metadata.extension}"


def generate_timelapse_proxy(timelapse_transfer: TimelapseTransfer, stem: str, dry_run: bool) -> Sequence[DCIMTransfer]:
    if not timelapse_transfer.jpg_files:
        click.secho("Generating timelapse proxy from RAW files not supported. Skipping proxy generation", fg="blue")
        return ()

    template_transfer = timelapse_transfer.jpg_files[0]
    output_path = Path("./") / f"{stem}{TIMELAPSE_PROXY_SUFFIX}"

    if not dry_run:
        subprocess.run(
            f"ffmpeg -framerate {TIMELAPSE_PROXY_FPS} "
            f"-pattern_type glob -i '{template_transfer.source_path.parent}/*{template_transfer.source_path.suffix}' "
            f"-c:v libx264 -pix_fmt yuv420p {output_path}",
            check=True,
            shell=True,
        )

    return (
        DCIMTransfer(
            source_path=output_path,
            metadata=Video(
                file_modify_date=template_transfer.metadata.file_modify_date,
                camera=template_transfer.metadata.camera,
                file_name=stem,
                extension=TIMELAPSE_PROXY_SUFFIX,
                mime_type="Timelapse-Proxy",
                exif_date=template_transfer.metadata.exif_date,
                resolution=template_transfer.metadata.resolution,
                fps=str(TIMELAPSE_PROXY_FPS),
            ),
            rectified_modify_date=template_transfer.rectified_modify_date,
            target_path=template_transfer.target_path.parent / f"{stem}{TIMELAPSE_PROXY_SUFFIX}",
        ),
    )


def patch_dcim_transfers_for_timelapse(dcim_transfers: Sequence[DCIMTransfer], dry_run: bool) -> Sequence[DCIMTransfer]:
    timelapse_transfer = get_timelapse_transfer_from_dcim_transfers(dcim_transfers=dcim_transfers)
    timelapse_spec = get_timelapse_spec_from_timelapse_transfer(timelapse_transfer=timelapse_transfer)

    timelapse_stem = (
        f"{get_timestamp_str(date=timelapse_spec.timestamp)}_{timelapse_spec.camera.name}_"
        f"{timelapse_spec.first_image_name}"
        f"{f'-{timelapse_spec.last_image_name}' if timelapse_spec.last_image_name else ''}"
        f"_timelapse_N{timelapse_spec.n_images}_{get_timelapse_duration_from_spec(timelapse_spec=timelapse_spec)}_"
        f"{timelapse_spec.dt}s_SS{timelapse_spec.shutter_speed}"
    )

    patched_dcim_transfers = (
        *(
            (
                patch_dcim_transfer_target_path(
                    timelapse_transfer.video_file,
                    target=Path(f"{timelapse_stem}{timelapse_transfer.video_file.metadata.extension}"),
                ),
            )
            if timelapse_transfer.video_file
            else generate_timelapse_proxy(
                timelapse_transfer=timelapse_transfer,
                stem=timelapse_stem,
                dry_run=dry_run,
            )
        ),
        *tuple(
            patch_dcim_transfer_target_path(
                dcim_transfer=dcim_transfer,
                target=Path(timelapse_stem) / "jpg" / get_timelapse_filename(dcim_transfer, timelapse_stem, n),
            )
            for n, dcim_transfer in enumerate(timelapse_transfer.jpg_files, start=1)
        ),
        *tuple(
            patch_dcim_transfer_target_path(
                dcim_transfer=dcim_transfer,
                target=Path(timelapse_stem) / "raw" / get_timelapse_filename(dcim_transfer, timelapse_stem, n),
            )
            for n, dcim_transfer in enumerate(timelapse_transfer.raw_files, start=1)
        ),
    )

    return patched_dcim_transfers
