import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from renum.utils import check_destination_collisions, execute_rename_plan


class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)

    def test_collision(self) -> None:
        source = self.directory / "source.txt"
        occupied = self.directory / "001.txt"
        source.write_text("source")
        occupied.write_text("keep this")

        with self.assertRaises(FileExistsError):
            check_destination_collisions([(source, occupied.name)])

        # The check should not change either file.
        self.assertEqual(source.read_text(), "source")
        self.assertEqual(occupied.read_text(), "keep this")

    def test_gap(self) -> None:
        second = self.directory / "002.jpg"
        third = self.directory / "003.jpg"
        second.write_text("second")
        third.write_text("third")

        execute_rename_plan(
            [
                (second, "001.jpg"),
                (third, "002.jpg"),
            ]
        )

        # Each file's contents should follow it to its new name.
        self.assertEqual((self.directory / "001.jpg").read_text(), "second")
        self.assertEqual((self.directory / "002.jpg").read_text(), "third")

        # Confirm the old `003.jpg` is gone
        self.assertFalse(third.exists())

    def test_swap(self) -> None:
        first = self.directory / "001.jpg"
        second = self.directory / "002.jpg"
        first.write_text("first")
        second.write_text("second")

        execute_rename_plan(
            [
                (first, "002.jpg"),
                (second, "001.jpg"),
            ]
        )

        self.assertEqual(first.read_text(), "second")
        self.assertEqual(second.read_text(), "first")

    def test_rollback(self) -> None:
        second = self.directory / "002.jpg"
        third = self.directory / "003.jpg"
        second.write_text("second")
        third.write_text("third")
        plan = [(second, "001.jpg"), (third, "002.jpg")]

        original_rename = Path.rename
        calls = 0

        def fail_once(path: Path, target: str | Path) -> Path:
            nonlocal calls
            calls += 1

            # Fail during the second final rename, after staging both files.
            if calls == 4:
                raise OSError("simulated failure")

            return original_rename(path, target)

        with (
            patch.object(Path, "rename", fail_once),
            self.assertRaisesRegex(OSError, "simulated failure"),
        ):
            execute_rename_plan(plan)

        # Rollback should restore the original names and contents.
        self.assertEqual(second.read_text(), "second")
        self.assertEqual(third.read_text(), "third")


if __name__ == "__main__":
    unittest.main()
