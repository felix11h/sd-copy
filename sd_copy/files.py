import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Sequence


def is_media_file(file: Path) -> bool:
    if file.stem.startswith("._"):
        logging.warning(f"Found non-media file {file.name}, skipping.")
        return False
    return True


def update_file_modify_date(file_path: Path, rectified_modify_date: datetime):
    os.utime(path=file_path, times=(rectified_modify_date.timestamp(), rectified_modify_date.timestamp()))


def copy_media_to_target(source_path: Path, target_path: Path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src=source_path, dst=target_path)  # copy2 also copies metadata (such as modified date)


def remove_source_file(source_path: Path):
    pass


def get_files_not_sorted(files_to_check: Sequence[Path], sorted_files: Sequence[Path]) -> Sequence[str]:
    return tuple(
        str(file)
        for file in files_to_check
        if is_media_file(file) and not any(file.stem in sorted_file.stem for sorted_file in sorted_files)
    )
