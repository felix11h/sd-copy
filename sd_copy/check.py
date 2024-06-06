import itertools
import json
from operator import attrgetter
from pathlib import Path
from typing import Callable, Optional, Sequence

from sd_copy.dcim_transfer import DCIMTransfer, Extension
from sd_copy.utils import TimestampConsistencyError


def sort_dcim_transfers(
    dcim_transfers: Sequence[DCIMTransfer],
    sort_key: Callable,
    exclude: Optional[Sequence[Extension]] = None,
) -> Sequence[DCIMTransfer]:
    return tuple(
        sorted(
            filter(lambda obj: obj.metadata.extension not in exclude, dcim_transfers) if exclude else dcim_transfers,
            key=sort_key,
        ),
    )


def write_json_to_file(dcim_transfers: Sequence[DCIMTransfer], file_name: str):
    Path(f"{file_name}.json").write_text(
        json.dumps(
            tuple(
                {
                    "file": str(dcim_transfer.source_path),
                    "target": dcim_transfer.target_path.name,
                    "rectified_timestamp": str(dcim_transfer.rectified_modify_date),
                }
                for dcim_transfer in dcim_transfers
            ),
            indent=2,
        ),
    )


def check_target_sorting_matches_source(dcim_transfers: Sequence[DCIMTransfer], exclude: Optional[Sequence[Extension]]):
    sorted_by_source = sort_dcim_transfers(dcim_transfers, sort_key=attrgetter("source_path"), exclude=exclude)
    sorted_by_target = sort_dcim_transfers(dcim_transfers, sort_key=attrgetter("target_path"), exclude=exclude)

    if sorted_by_source != sorted_by_target:
        write_json_to_file(sorted_by_target, "sorted_by_target")
        write_json_to_file(sorted_by_source, "sorted_by_source")
        raise TimestampConsistencyError(
            "Unexpected changes in sorting between source and target, likely due to incorrect timestamp. "
            "Output written to 'sorted_by_source.json' and 'sorted_by_target.json'",
        )


def check_dcim_transfers(dcim_transfers: Sequence[DCIMTransfer], timelapse: bool):
    """Assert that copied files maintain the sorting of the source files. Either raw or compressed images need to
    be excluded, as cameras can create them at the same time using the same filename. Depending on metadata included
    in the target filename, this can lead to changes in the sorting:
      [source path]
      ├── DSCF0231.JPG
      ├── DSCF0231.RAF
    becomes
      [target path]
      ├── 20210708-174028_x-t3_DSCF0231_4416x2944.raf
      ├── 20210708-174028_x-t3_DSCF0231_6240x4160.jpg

    The same concept applies to DNG raw files from DJI. In timelapse mode, there can only be one video, which
    needs to be excluded, as sorting positions among the image files might change from source to target.

    In case the sorting does not match the source, this may point to camera recording errors, or issues
    with this program!"""
    for image_extenions in itertools.combinations((Extension.jpg, Extension.raf, Extension.dng), 2):
        check_target_sorting_matches_source(
            dcim_transfers=dcim_transfers,
            exclude=(*image_extenions, *((Extension.mp4, Extension.mov) if timelapse else ())),
        )
