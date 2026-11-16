import importlib.metadata
import os
import sys
from argparse import ArgumentTypeError
from collections import Counter
from pathlib import Path


def get_version() -> str:
    """Return the package version from installed metadata."""

    try:
        return importlib.metadata.version("renum")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def permission_check(path: Path) -> bool:
    """Check read/write permissions for a given path."""

    return os.access(path, os.R_OK | os.W_OK)


def positive_int_check(value: str) -> int:
    """argparse type: int > 0."""

    try:
        int_value = int(value)
    except ValueError:
        raise ArgumentTypeError(f"value must be an integer, got '{value}'")

    if int_value <= 0:
        raise ArgumentTypeError(f"value must be at least 1, got {int_value}")
    return int_value


def validate_directory(directory: Path, displayed_path: str) -> None:
    """Exit with an error if the target is missing, not a directory, or unwritable."""

    if not directory.exists() or not directory.is_dir():
        print(f"Error: `{displayed_path}` does not exist or is not a directory.")
        sys.exit(1)

    if not permission_check(directory):
        print(f"Error: read/write permissions error on `{displayed_path}` directory.")
        sys.exit(2)


def find_matching_files(
    directory: Path, extensions: list[str]
) -> tuple[list[Path], Counter]:
    """Collect matching files in case-insensitive alphabetical order."""

    files: list[Path] = []
    counts = Counter(dict.fromkeys(extensions, 0))

    # Keep the preflight permission check so obvious permission problems are
    # found before starting the rename loop. It cannot eliminate race conditions
    # if permissions or files change after this check.
    for item in sorted(directory.iterdir(), key=lambda file: file.name.casefold()):
        if not item.is_file() or item.suffix.removeprefix(".") not in extensions:
            continue

        if not permission_check(item):
            print(f"Error: read/write permissions error on `{item}` file.")
            sys.exit(2)

        files.append(item)
        counts[item.suffix.removeprefix(".")] += 1

    return files, counts


def build_rename_plan(files: list[Path], digits: int) -> list[tuple[Path, str]]:
    """Pair each source file with its planned sequential filename."""

    return [
        (file, f"{str(index).zfill(digits)}{file.suffix}")
        for index, file in enumerate(files, 1)
    ]
