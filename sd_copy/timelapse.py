import re
from operator import attrgetter
from typing import Sequence

import click

from sd_copy.dcim_transfer import DCIMTransfer, Image, get_sorted_transfers, get_target_path, get_timestamp_str
from sd_copy.utils import UnexpectedDataError, get_single_value


def get_image_number(image_path) -> int:
    return int(re.match("^DSCF(\\d{4})\\.", image_path.name).group(1))


def get_timedeltas_rounded_value(timedeltas: Sequence[float]) -> int:
    click.secho("[Note] ", fg="blue", nl=False)
    click.secho(f"Multiple dt found in timeline {set(timedeltas)}, using rounded value")
    return round(sum(timedeltas) / len(timedeltas))


def check_timelapse_consistency(dcim_transfers: Sequence[DCIMTransfer]):
    if not_images := tuple(transfer for transfer in dcim_transfers if not isinstance(transfer.metadata, Image)):
        raise UnexpectedDataError(
            "Working in timelapse mode, but input contains files that are not images:"
            "\n\t".join(tuple(dcim_transfer.source_path.name for dcim_transfer in not_images)),
        )

    if len(img_formats := set(transfer.source_path.suffix for transfer in dcim_transfers)) > 1:
        raise UnexpectedDataError(f"Found multiple img formats: {img_formats}")


def get_timelapse_dt(sorted_dcim_transfers: Sequence[DCIMTransfer]) -> int:
    timedeltas = tuple(
        (next_image.rectified_modify_date - image.rectified_modify_date).total_seconds()
        for next_image, image in zip(sorted_dcim_transfers[1:], sorted_dcim_transfers[:-1])
    )

    if max(timedeltas) - min(timedeltas) > 1:
        raise UnexpectedDataError(
            "Images interval unexpected, time-lapse might need to be split up:"
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
        else get_timedeltas_rounded_value(timedeltas)
    )


def patch_dcim_transfers_target_path(dcim_transfers: Sequence[DCIMTransfer]) -> Sequence[DCIMTransfer]:
    sorted_dcim_transfers = get_sorted_transfers(dcim_transfers, sort_key=attrgetter("rectified_modify_date"))
    timelapse_folder_name = "_".join(
        (
            get_timestamp_str(
                date=sorted_dcim_transfers[0].rectified_modify_date,
                metadata=sorted_dcim_transfers[0].metadata,
                timelapse=False,
            ),
            sorted_dcim_transfers[0].metadata.camera.name,
            sorted_dcim_transfers[0].metadata.file_name,
            "time-lapse",
            f"N{len(sorted_dcim_transfers)}",
            f"{get_timelapse_dt(sorted_dcim_transfers=sorted_dcim_transfers)}s",
        ),
    )

    for n, transfer in enumerate(sorted_dcim_transfers, start=1):
        transfer.target_path = (
            transfer.target_path.parent
            / timelapse_folder_name
            / get_target_path(
                destination=transfer.target_path,
                metadata=transfer.metadata,
                rectified_date=transfer.rectified_modify_date,
                timelapse=True,
                timelapse_n=n,
            ).name
        )

    return dcim_transfers
