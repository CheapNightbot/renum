import argparse
import os
import sys
import textwrap
from pathlib import Path

from renum.utils import (
    build_rename_plan,
    check_destination_collisions,
    execute_rename_plan,
    find_matching_files,
    get_version,
    positive_int_check,
    validate_directory,
)


def main(argv: list[str] | None = None) -> None:
    """Program entry point (referenced in pyproject.toml [project.scripts]).

    Parses ``argv`` (defaults to `sys.argv[1:]`) and runs the core logic.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Use an absolute path so it remains valid after changing into the directory.
    directory = Path(args.dir).absolute()
    validate_directory(directory, args.dir)

    # `Path.rename()` below uses relative destination names, so change into the
    # target directory to ensure files are renamed there, not in the caller's
    # working directory.
    os.chdir(directory)

    files, counts = find_matching_files(directory, args.ext)
    if not files:
        print(
            f"There were no files in `{args.dir}` directory "
            f"matching extension(s): {args.ext}"
        )
        sys.exit(3)

    plan = build_rename_plan(files, args.digits)

    try:
        check_destination_collisions(plan)
    except FileExistsError as error:
        print(f"\nError: {error}")
        sys.exit(5)

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

    try:
        execute_rename_plan(plan)
    except FileExistsError as error:
        print(f"\nError: {error}")
        sys.exit(5)
    except RuntimeError as error:
        print(f"\nError: {error}")
        sys.exit(6)
    except OSError as error:
        print(f"\nError while renaming files: {error}")
        sys.exit(7)

    print(
        f"\n> Successfully renamed {len(plan)} file(s) in the following "
        f"directory:\n{directory}"
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
