import logging
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from sd_copy.utils import get_optional_single_value


@dataclass
class RenameOperation:
    old_path: Path
    new_path: Path


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


def get_top_level_folders(path: Path) -> Sequence[Path]:
    return tuple(path for path in path.glob("*") if path.is_dir())


def get_renamed_folder_path(old_folder_path: Path, source_folders: Sequence[Path]) -> Optional[Path]:
    source_folder_match = get_optional_single_value(
        tuple(
            source_folder_path.name
            for source_folder_path in source_folders
            if re.match(r"^(\d{4}-\d{2}-\d{2}).*", old_folder_path.name).group(1) in source_folder_path.name
        ),
    )
    if source_folder_match and source_folder_match != old_folder_path.name:
        return old_folder_path.parent / source_folder_match


def get_rename_operations(source_folders: Sequence[Path], target_folders: Sequence[Path]) -> Sequence[RenameOperation]:
    return tuple(
        RenameOperation(old_path=old_folder_path, new_path=renamed_folder_path)
        for old_folder_path in target_folders
        if (renamed_folder_path := get_renamed_folder_path(old_folder_path, source_folders))
    )


def get_files_not_sorted(files_to_check: Sequence[Path], sorted_files: Sequence[Path]) -> Sequence[str]:
    return tuple(
        str(file)
        for file in files_to_check
        if is_media_file(file) and not any(file.stem in sorted_file.stem for sorted_file in sorted_files)
    )
