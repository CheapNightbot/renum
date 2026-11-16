import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from renum.cli import main


class TestCli(unittest.TestCase):
    def setUp(self) -> None:
        self.original_directory = Path.cwd()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(os.chdir, self.original_directory)
        self.directory = Path(temp.name)

    def run_cli(self, *options: str) -> tuple[int, str]:
        output = io.StringIO()

        with (
            contextlib.redirect_stdout(output),
            self.assertRaises(SystemExit) as result,
        ):
            main(
                [
                    "--ext",
                    "jpg",
                    "--digits",
                    "3",
                    *options,
                    str(self.directory),
                ]
            )

        code = result.exception.code
        if not isinstance(code, int):
            raise TypeError(f"Expected an integer exit code, got {code!r}")

        return code, output.getvalue()

    def test_dry_run(self) -> None:
        image = self.directory / "wallpaper.jpg"
        image.write_text("image")

        code, output = self.run_cli("--dry-run")

        self.assertEqual(code, 0)
        self.assertIn("wallpaper.jpg", output)
        self.assertIn("001.jpg", output)
        self.assertTrue(image.exists())  # Preview must not rename.

    def test_assume_yes(self) -> None:
        (self.directory / "wallpaper.jpg").write_text("image")

        code, _ = self.run_cli("--assume-yes")

        self.assertEqual(code, 0)
        self.assertEqual((self.directory / "001.jpg").read_text(), "image")

    def test_collision(self) -> None:
        source = self.directory / "wallpaper.jpg"
        source.write_text("image")
        (self.directory / "001.jpg").mkdir()  # Occupies the planned destination.

        with patch("builtins.input", side_effect=AssertionError("should not prompt")):
            code, output = self.run_cli()

        self.assertEqual(code, 5)
        self.assertIn("already exists", output)
        self.assertTrue(source.exists())  # Collision must leave source untouched.


if __name__ == "__main__":
    unittest.main()
