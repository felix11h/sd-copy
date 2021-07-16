import shutil
from datetime import datetime


class UnexpectedDataError(ValueError):
    """Raise when input data presents a case not yet handled."""


class MissingDependencyError(RuntimeError):
    """Raise when dependencies are missing"""


def check_if_exiftool_installed():
    if not shutil.which("exiftool"):
        raise MissingDependencyError("Exiftool not found, please install")


def get_datetime_from_str(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
