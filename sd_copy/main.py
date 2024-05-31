import logging
from pathlib import Path

import click

from sd_copy.dcim_transfer import Extension, check_target_sorting_matches_source, get_dcim_transfers, is_media_file
from sd_copy.files import copy_media_to_target, get_files_not_sorted, remove_source_file, update_file_modify_date
from sd_copy.timelapse import check_timelapse_consistency, patch_dcim_transfers_target_path
from sd_copy.utils import CopyError, check_if_exiftool_installed, get_checksum

TIME_OFFSET_HELP = (
    "Timedelta in seconds to add to the modification date. Determine for example via "
    "`(datetime.strptime(desired_date, format) - datetime.strptime(recorded_date, format)).total_seconds()`."
)


@click.group()
def main():
    pass


@main.command("check-sorted")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(exists=True, path_type=Path))
def check_sorted_dcim(src: Path, dst: Path):
    """Use original filename to check if a file has been sorted. For example, a file DCSF1234.MOV is sorted to
    a new filename 20240101-1200_x-t3_DCSF1234_[...].mov, which contains the 'DCSF1234' part."""
    click.secho("Note: Timelapse photos are not supported as they do not contain the original filename", fg="blue")
    click.secho("Checking files ... ", nl=False)

    sorted_files = tuple(file for file in dst.rglob("*") if is_media_file(file))

    if unsorted_files := get_files_not_sorted(files_to_check=tuple(src.rglob("*")), sorted_files=sorted_files):
        click.secho("Unsorted files found!", fg="red")
        click.secho("\n".join(unsorted_files))
    else:
        click.secho("Ok! All files already sorted!", fg="green")


@main.command("sort")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(exists=True, path_type=Path))
@click.option("--time-offset", "-td", default=0, type=int, help=TIME_OFFSET_HELP)
@click.option("--timelapse", default=False, is_flag=True)
@click.option("--dry-run", "-n", default=False, is_flag=True)
@click.option("--delete", "-d", default=False, is_flag=True)
@click.option("--debug", "-v", default=False, is_flag=True)
def sort_dcim(src: Path, dst: Path, time_offset: int, timelapse: bool, dry_run: bool, delete: bool, debug: bool):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s: %(message)s" if debug else "%(message)s",
    )

    check_if_exiftool_installed()
    dcim_transfers = get_dcim_transfers(
        source_path=src,
        destination_path=dst,
        time_offset=time_offset,
        timelapse=timelapse,
    )

    if timelapse:
        check_timelapse_consistency(dcim_transfers=dcim_transfers)
        dcim_transfers = patch_dcim_transfers_target_path(dcim_transfers=dcim_transfers)

    # Assert that copied files maintain the sorting of the source files. Either raw or compressed images need to
    # be excluded, as cameras can create them at the same time using the same filename. Depending on metadata included
    # in the target filename, this can lead to changes in the sorting:
    #   [source path]
    #   ├── DSCF0231.JPG
    #   ├── DSCF0231.RAF
    # becomes
    #   [target path]
    #   ├── 20210708-174028_x-t3_DSCF0231_4416x2944.raf
    #   ├── 20210708-174028_x-t3_DSCF0231_6240x4160.jpg
    # If sorting does not match the source, this may point to camera recording errors, or issues with this program
    check_target_sorting_matches_source(dcim_transfers=dcim_transfers, exclude=Extension.jpg)
    check_target_sorting_matches_source(dcim_transfers=dcim_transfers, exclude=Extension.raf)

    for dcim_transfer in dcim_transfers:
        if not dry_run:
            source_checksum = get_checksum(file=dcim_transfer.source_path)
            click.secho(f"Copying {dcim_transfer.source_path} to {dcim_transfer.target_path} ... ", nl=False)
            copy_media_to_target(source_path=dcim_transfer.source_path, target_path=dcim_transfer.target_path)
            click.secho("OK", fg="green", nl=False)
            update_file_modify_date(
                file_path=dcim_transfer.target_path,
                rectified_modify_date=dcim_transfer.rectified_modify_date,
            )
            click.secho("  Checksum ... ", nl=False)
            target_checksum = get_checksum(file=dcim_transfer.target_path)
            click.secho("OK", fg="green")
            if source_checksum != target_checksum:
                raise CopyError(f"Target checksum does not match source checksum for {dcim_transfer.source_path.name}")
            if delete:
                remove_source_file(source_path=dcim_transfer.source_path)

        else:
            print(f"{dcim_transfer.source_path} --> {dcim_transfer.target_path}")


if __name__ == "__main__":
    main()
