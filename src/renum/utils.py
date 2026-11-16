import importlib.metadata
import os
from argparse import ArgumentTypeError
from pathlib import Path


def get_version() -> str:
    """Return the package version from installed metadata"""
    try:
        return importlib.metadata.version("renum")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def permission_check(path: Path) -> bool:
    """Check read/write permissions for a given Path."""
    return os.access(path, os.R_OK | os.W_OK)


def positive_int_check(value):
    """argparse type: int > 0."""
    try:
        ivalue = int(value)
    except ValueError:
        raise ArgumentTypeError(f"value must be an integer, got '{value}'")

    if ivalue <= 0:
        raise ArgumentTypeError(f"value must be at least 1, got {ivalue}")
    return ivalue
