import argparse
import os
import sys
import textwrap
from collections import Counter
from pathlib import Path

from renum.utils import get_version, permission_check, positive_int_check


def main(argv: list[str] | None = None) -> None:
    """Program entry point (referenced in pyproject.toml [project.scripts]).

    Parses ``argv`` (defaults to `sys.argv[1:]`) and runs the core logic.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Use absolute path, otherwise iterdir will fail as after changing to this
    # directory it will look relative to this directory for this directory !? www
    directory = Path(args.dir).absolute()
    if not directory.exists() or not directory.is_dir():
        print(f"Error: `{args.dir}` does not exist or is not a directory.")
        sys.exit(1)

    # For these checks, me aware of TOCTOU (and using try/except).
    # But the reason for doing this is, to make sure we don't modify
    # files and half-way-through hit such errors. Which can leave some
    # files changed and rest unchanged. We only want to rename when
    # everything is safe and we can rename all the matching files.
    if not permission_check(directory):
        print(f"Error: read/write permissions error on `{args.dir}` directory.")
        sys.exit(2)

    # Renaming file (Path.rename) was moving file to the directory from where
    # the command ran. There might be a better solution than this.
    os.chdir(directory)

    files: list[Path] = []
    counts = Counter(dict.fromkeys(args.ext, 0))
    for item in sorted(directory.iterdir(), key=lambda file: file.name.casefold()):
        if not item.is_file() or item.suffix.removeprefix(".") not in args.ext:
            continue

        if not permission_check(item):
            print(f"Error: read/write permissions error on `{item}` file.")
            sys.exit(2)

        files.append(item)
        counts[item.suffix.removeprefix(".")] += 1

    if len(files) == 0:
        print(
            f"There were no files in `{args.dir}` directory matching extension(s): {args.ext}"
        )
        sys.exit(3)

    plan = [
        (file, f"{str(idx).zfill(args.digits)}{file.suffix}")
        for idx, file in enumerate(files, 1)
    ]

    print()  # Just for a newline ~
    for file, new_name in plan:
        print(f"{file.name:32}\t -> \t{new_name}")

    # Some stats, why not !?
    print(f"\n{'-' * 32}\n")
    print(dict(counts))
    print(f"Total files: {len(files)}")

    if args.dry_run:
        print(
            "\n> No files were renamed, because you ran command with `--dry-run` flag."
        )
        sys.exit(0)

    if not args.assume_yes:
        try:
            answer = (
                input(f"\nRename {len(plan)} file(s) in {directory}? [y/N] ")
                .strip()
                .casefold()
            )
        except EOFError:
            print(
                "\nError: confirmation required. Use `--assume-yes` to skip the prompt."
            )
            sys.exit(4)
        except KeyboardInterrupt:
            answer = "absolutely no! 🙂"

        if answer not in {"y", "yes"}:
            print("\n> Cancelled. No files were renamed.")
            sys.exit(0)

    for file, new_name in plan:
        file.rename(new_name)

    print(
        f"\n> Successfully renamed {len(plan)} file(s) in the following directory:\n"
        f"{directory}"
    )
    sys.exit(0)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        prog="renum",
        description="Batch-rename files in a directory to sequential, zero-padded numbers",
        epilog=textwrap.dedent("""\
        examples:
          renum --ext "jpg,png,gif" --digits 3 ~/Pictures
          renum --ext "txt" --digits 2 ./notes
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group()

    # Optional, placed at top to show right after help option.
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    # Positional argument
    parser.add_argument(
        "dir",
        nargs="?",  # Optional (can omit)
        default=".",  # Default if omitted
        metavar="DIRECTORY",
        help="Target directory (default: current directory)",
    )

    # Required arguments
    parser.add_argument(
        "--ext",
        metavar="EXTENSIONS",
        required=True,
        type=lambda ext: ext.strip(",").split(","),
        help="Comma-separated list of extensions to include",
    )

    parser.add_argument(
        "--digits",
        metavar="N",
        type=positive_int_check,
        required=True,
        help="Number of digits for the counter (zero-padded)",
    )

    # Optional arguments
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without touching anything",
    )

    group.add_argument(
        "--assume-yes",
        action="store_true",
        help="Rename files without asking for confirmation",
    )

    return parser
