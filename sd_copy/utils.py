import shutil
from datetime import datetime
from hashlib import md5
from pathlib import Path
from typing import Collection, Optional, T

CHUNK_SIZE = 8192


class UnexpectedDataError(ValueError):
    """Raise when input data presents a case not yet handled."""


class MissingDependencyError(RuntimeError):
    """Raise when dependencies are missing"""


class TimestampConsistencyError(Exception):
    pass


class NonSingleValueError(Exception):
    pass


class CopyError(Exception):
    pass


def check_if_exiftool_installed():
    if not shutil.which("exiftool"):
        raise MissingDependencyError("Exiftool not found, please install")


def get_datetime_from_str(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")


def get_single_value(values: Collection[T]) -> T:
    try:
        (value,) = values
    except ValueError as e:
        raise NonSingleValueError(f"Single element expected, found: {values}") from e
    return value


def get_optional_single_value(values: Collection[T]) -> Optional[T]:
    if values:
        try:
            (value,) = values
        except ValueError as e:
            raise NonSingleValueError(f"Single element expected, found: {values}") from e
        return value


def get_checksum(file: Path) -> str:
    checksum = md5()
    with file.open(mode="rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            checksum.update(chunk)
    return checksum.hexdigest()
