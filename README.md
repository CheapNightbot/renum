# renum

Rename files in a directory to sequential numbers, keeping their extensions (e.g.: `001.jpg, 002.png, 003.jpg`).


Choose a directory, the extensions to include, and the number of digits to use. `renum` sorts matching filenames alphabetically, ignoring case, before numbering them.

> [!IMPORTANT]
> **Preview before renaming.** Use `--dry-run` to check the planned changes, and keep a backup of important files. `renum` does not currently check for existing destination names or roll back if a rename fails partway through.

<details>
  <summary>I swear me have a life!</summary>
  <img src="renum whiteboard.svg" alt="The renum planning whiteboard" />
</details>

## How to use

### Install it

With [pipx](https://pipx.pypa.io/):

```sh
pipx install git+https://github.com/CheapNightbot/renum
```

Or with [uv](https://docs.astral.sh/uv/):

```sh
uv tool install git+https://github.com/CheapNightbot/renum
```

After installing, run it with `renum`.

### Run without installing

Clone the project, enter its directory, and use `uv run`:

```sh
git clone https://github.com/CheapNightbot/renum.git
cd renum
uv run renum --help
```

`uv` will set up the project environment as needed. You can also use `uv run renum ...` for the examples below.

## Usage

```text
renum [DIRECTORY] --ext EXTENSIONS --digits N [--dry-run]
```

- `DIRECTORY` is the folder to process. If omitted, `renum` uses the current directory.
- `--ext` is a comma-separated list of extensions, without leading dots. For example: `jpg,png`.
- `--digits` sets the minimum number of digits in each number. For example, `--digits 3` numbers files `001`, `002`, `003`, and so on.
- `--dry-run` shows the planned old and new names without renaming anything.

Only files directly inside the target directory are considered; subdirectories are not searched. Extension matching is case-sensitive, so `jpg` does not match `.JPG`.

<details>
  <summary>Show examples</summary>

### Preview, then rename

Suppose `~/Pictures` contains:

```text
beach.png
Cat.jpg
portrait.jpg
```

Preview the changes:

```sh
renum --ext "jpg,png" --digits 3 --dry-run ~/Pictures
```

The files are sorted alphabetically, ignoring case, and the preview shows:

```text
beach.png                         -> 001.png
Cat.jpg                           -> 002.jpg
portrait.jpg                      -> 003.jpg
```

If the preview looks right, run the command again without `--dry-run`:

```sh
renum --ext "jpg,png" --digits 3 ~/Pictures
```

The files are then named:

```text
001.png
002.jpg
003.jpg
```

### Use a different number width

Suppose a folder contains:

```text
notes-a.txt
notes-b.txt
notes-c.txt
```

Preview the changes:

```sh
renum --ext "txt" --digits 2 --dry-run ./notes
```

The preview is:

```text
notes-a.txt                      -> 01.txt
notes-b.txt                      -> 02.txt
notes-c.txt                      -> 03.txt
```

Remove `--dry-run` to apply the changes.

</details>
