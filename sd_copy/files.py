import logging
from pathlib import Path
from typing import Sequence


def is_media_file(file: Path) -> bool:
    if file.stem.startswith("._"):
        logging.warning(f"Found non-media file {file.name}, skipping.")
        return False
    return True


def get_files_not_sorted(files_to_check: Sequence[Path], sorted_files: Sequence[Path]) -> Sequence[str]:
    return tuple(
        str(file)
        for file in files_to_check
        if is_media_file(file) and not any(file.stem in sorted_file.stem for sorted_file in sorted_files)
    )
