import shutil
from datetime import datetime
from typing import Collection, T


class UnexpectedDataError(ValueError):
    """Raise when input data presents a case not yet handled."""


class MissingDependencyError(RuntimeError):
    """Raise when dependencies are missing"""


class NonSingleValueError(Exception):
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
