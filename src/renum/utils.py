import importlib.metadata
import os
import sys
import uuid
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
    counts = (
        Counter(dict.fromkeys(extensions, 0)) if extensions[0] != "*" else Counter()
    )

    # Keep the preflight permission check so obvious permission problems are
    # found before starting the rename loop. It cannot eliminate race conditions
    # if permissions or files change after this check.
    for item in sorted(directory.iterdir(), key=lambda file: file.name.casefold()):
        if not item.is_file() or (
            extensions[0] != "*" and item.suffix.removeprefix(".") not in extensions
        ):
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


def _path_exists(path: Path) -> bool:
    """Return True for existing paths, including broken symlinks."""

    return path.exists() or path.is_symlink()


def check_destination_collisions(plan: list[tuple[Path, str]]) -> None:
    """Refuse destinations occupied by files outside this rename plan."""

    sources = {source for source, _ in plan}

    for source, new_name in plan:
        destination = source.with_name(new_name)

        # A file may keep its current name. Other existing destinations are
        # okay only when that path is itself a source in this batch.
        if (
            _path_exists(destination)
            and destination != source
            and destination not in sources
        ):
            raise FileExistsError(
                f"destination `{destination.name}` already exists and "
                "is not being renamed by this run"
            )


def execute_rename_plan(plan: list[tuple[Path, str]]) -> None:
    """Rename through temporary paths so planned names can safely overlap."""

    check_destination_collisions(plan)

    # Convert destination names to paths beside their source files. Keeping
    # temporary and final names in the same directory avoids cross-filesystem
    # moves and makes each individual rename atomic on typical filesystems.
    path_plan = [
        (source, source.with_name(new_name))
        for source, new_name in plan
        if source != source.with_name(new_name)
    ]

    staged: list[tuple[Path, Path]] = []
    completed: list[tuple[Path, Path]] = []

    try:
        # First free all the names that this batch will need.
        for source, _ in path_plan:
            temporary = source.with_name(f".renum-{uuid.uuid4().hex}.tmp")
            while _path_exists(temporary):
                temporary = source.with_name(f".renum-{uuid.uuid4().hex}.tmp")

            source.rename(temporary)
            staged.append((source, temporary))

        # Then assign the final names.
        for source, temporary in staged:
            destination = next(
                destination
                for planned_source, destination in path_plan
                if planned_source == source
            )
            temporary.rename(destination)
            completed.append((temporary, destination))

    except OSError as original_error:
        # Best effort: move completed files back to their temporary names,
        # then restore every staged file to its original name.
        rollback_errors: list[str] = []

        for temporary, destination in reversed(completed):
            try:
                if _path_exists(temporary):
                    raise FileExistsError(f"temporary path `{temporary}` is occupied")
                destination.rename(temporary)
            except OSError as error:
                rollback_errors.append(
                    f"could not move `{destination.name}` back to "
                    f"`{temporary.name}`: {error}"
                )

        for source, temporary in reversed(staged):
            try:
                if not _path_exists(temporary):
                    continue
                if _path_exists(source):
                    raise FileExistsError(f"original path `{source}` is occupied")
                temporary.rename(source)
            except OSError as error:
                rollback_errors.append(
                    f"could not restore `{source.name}` from "
                    f"`{temporary.name}`: {error}"
                )

        if rollback_errors:
            details = "\n".join(f"- {message}" for message in rollback_errors)
            raise RuntimeError(
                f"rename failed: {original_error}\n"
                "Rollback was incomplete; check these paths manually:\n"
                f"{details}"
            ) from original_error

        raise
