import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

import click

from sd_copy.dcim_transfer import Extension, assert_target_sorting_matches_source, get_dcim_transfers
from sd_copy.utils import CopyError, check_if_exiftool_installed, get_checksum


def copy_media_to_target(source_path: Path, target_path: Path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src=source_path, dst=target_path)  # copy2 also copies metadata (such as modified date)


def update_file_modify_date(file_path: Path, rectified_modify_date: datetime):
    os.utime(path=file_path, times=(rectified_modify_date.timestamp(), rectified_modify_date.timestamp()))


def remove_source_file(source_path: Path):
    pass


@click.command()
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", "-n", default=False, is_flag=True)
@click.option("--delete", "-d", default=False, is_flag=True)
@click.option("--debug", "-v", default=False, is_flag=True)
def main(src: Path, dst: Path, dry_run: bool, delete: bool, debug: bool):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s: %(message)s" if debug else "%(message)s",
    )

    check_if_exiftool_installed()
    dcim_transfers = get_dcim_transfers(source_path=src, destination_path=dst)

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
    assert_target_sorting_matches_source(dcim_transfers=dcim_transfers, exclude=Extension.jpg)
    assert_target_sorting_matches_source(dcim_transfers=dcim_transfers, exclude=Extension.raf)

    for dcim_transfer in dcim_transfers:
        if not dry_run:
            source_checksum = get_checksum(file=dcim_transfer.source_path)
            copy_media_to_target(source_path=dcim_transfer.source_path, target_path=dcim_transfer.target_path)
            update_file_modify_date(
                file_path=dcim_transfer.target_path,
                rectified_modify_date=dcim_transfer.rectified_modify_date,
            )
            target_checksum = get_checksum(file=dcim_transfer.target_path)
            if source_checksum != target_checksum:
                raise CopyError(f"Target checksum does not match source checksum for {dcim_transfer.source_path.name}")
            if delete:
                remove_source_file(source_path=dcim_transfer.source_path)

        else:
            print(f"{dcim_transfer.source_path} --> {dcim_transfer.target_path}")


if __name__ == "__main__":
    main()
