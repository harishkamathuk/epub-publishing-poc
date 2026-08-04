from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_book


class ValidateBookTests(unittest.TestCase):
    def test_missing_epubcheck_jar_environment_variable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epub_path = repo_root / "dist" / "epub-publishing-poc.epub"
            epub_path.parent.mkdir(parents=True)
            epub_path.write_bytes(b"epub")
            stderr = io.StringIO()

            with (
                mock.patch.object(validate_book, "REPO_ROOT", repo_root),
                mock.patch.object(validate_book, "DEFAULT_EPUB", epub_path),
                mock.patch.dict(os.environ, {}, clear=True),
                contextlib.redirect_stderr(stderr),
            ):
                result = validate_book.main()

        self.assertEqual(result, 1)
        self.assertIn("EPUBCHECK_JAR is not set.", stderr.getvalue())

    def test_jar_path_does_not_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epub_path = repo_root / "dist" / "epub-publishing-poc.epub"
            epub_path.parent.mkdir(parents=True)
            epub_path.write_bytes(b"epub")
            missing_jar = repo_root / "tools" / "epubcheck.jar"
            stderr = io.StringIO()

            with (
                mock.patch.object(validate_book, "REPO_ROOT", repo_root),
                mock.patch.object(validate_book, "DEFAULT_EPUB", epub_path),
                mock.patch.dict(os.environ, {"EPUBCHECK_JAR": str(missing_jar)}, clear=True),
                contextlib.redirect_stderr(stderr),
            ):
                result = validate_book.main()

        self.assertEqual(result, 1)
        self.assertIn("EPUBCheck JAR is missing", stderr.getvalue())

    def test_jar_path_that_is_a_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epub_path = repo_root / "dist" / "epub-publishing-poc.epub"
            jar_dir = repo_root / "tools" / "epubcheck.jar"
            epub_path.parent.mkdir(parents=True)
            jar_dir.mkdir(parents=True)
            epub_path.write_bytes(b"epub")
            stderr = io.StringIO()

            with (
                mock.patch.object(validate_book, "REPO_ROOT", repo_root),
                mock.patch.object(validate_book, "DEFAULT_EPUB", epub_path),
                mock.patch.dict(os.environ, {"EPUBCHECK_JAR": str(jar_dir)}, clear=True),
                contextlib.redirect_stderr(stderr),
            ):
                result = validate_book.main()

        self.assertEqual(result, 1)
        self.assertIn("EPUBCheck JAR is not a file", stderr.getvalue())

    def test_java_is_not_available_on_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epub_path = repo_root / "dist" / "epub-publishing-poc.epub"
            jar_path = repo_root / "tools" / "epubcheck.jar"
            epub_path.parent.mkdir(parents=True)
            jar_path.parent.mkdir(parents=True)
            epub_path.write_bytes(b"epub")
            jar_path.write_bytes(b"jar")
            stderr = io.StringIO()

            with (
                mock.patch.object(validate_book, "REPO_ROOT", repo_root),
                mock.patch.object(validate_book, "DEFAULT_EPUB", epub_path),
                mock.patch.dict(os.environ, {"EPUBCHECK_JAR": str(jar_path)}, clear=True),
                mock.patch("scripts.validate_book.shutil.which", return_value=None),
                contextlib.redirect_stderr(stderr),
            ):
                result = validate_book.main()

        self.assertEqual(result, 1)
        self.assertIn("Java is not available on PATH.", stderr.getvalue())

    def test_epub_file_does_not_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epub_path = repo_root / "dist" / "epub-publishing-poc.epub"
            stderr = io.StringIO()

            with (
                mock.patch.object(validate_book, "REPO_ROOT", repo_root),
                mock.patch.object(validate_book, "DEFAULT_EPUB", epub_path),
                contextlib.redirect_stderr(stderr),
            ):
                result = validate_book.main()

        self.assertEqual(result, 1)
        self.assertIn("EPUB file is missing", stderr.getvalue())

    def test_successful_epubcheck_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epub_path = repo_root / "dist" / "epub-publishing-poc.epub"
            jar_path = repo_root / "tools" / "epubcheck.jar"
            epub_path.parent.mkdir(parents=True)
            jar_path.parent.mkdir(parents=True)
            epub_path.write_bytes(b"epub")
            jar_path.write_bytes(b"jar")

            with (
                mock.patch.object(validate_book, "REPO_ROOT", repo_root),
                mock.patch.object(validate_book, "DEFAULT_EPUB", epub_path),
                mock.patch.dict(os.environ, {"EPUBCHECK_JAR": str(jar_path)}, clear=True),
                mock.patch("scripts.validate_book.shutil.which", return_value="java"),
                mock.patch(
                    "scripts.validate_book.subprocess.run",
                    return_value=mock.Mock(returncode=0),
                ) as run_mock,
            ):
                result = validate_book.main()

        self.assertEqual(result, 0)
        run_mock.assert_called_once_with(
            ["java", "-jar", str(jar_path.resolve()), str(epub_path)],
            cwd=repo_root,
            check=False,
        )

    def test_non_zero_epubcheck_exit_code_is_returned_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epub_path = repo_root / "dist" / "epub-publishing-poc.epub"
            jar_path = repo_root / "tools" / "epubcheck.jar"
            epub_path.parent.mkdir(parents=True)
            jar_path.parent.mkdir(parents=True)
            epub_path.write_bytes(b"epub")
            jar_path.write_bytes(b"jar")

            with (
                mock.patch.object(validate_book, "REPO_ROOT", repo_root),
                mock.patch.object(validate_book, "DEFAULT_EPUB", epub_path),
                mock.patch.dict(os.environ, {"EPUBCHECK_JAR": str(jar_path)}, clear=True),
                mock.patch("scripts.validate_book.shutil.which", return_value="java"),
                mock.patch(
                    "scripts.validate_book.subprocess.run",
                    return_value=mock.Mock(returncode=7),
                ),
            ):
                result = validate_book.main()

        self.assertEqual(result, 7)

    def test_subprocess_run_is_called_without_shell_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            epub_path = repo_root / "dist" / "epub-publishing-poc.epub"
            jar_path = repo_root / "tools" / "epubcheck.jar"
            epub_path.parent.mkdir(parents=True)
            jar_path.parent.mkdir(parents=True)
            epub_path.write_bytes(b"epub")
            jar_path.write_bytes(b"jar")

            with (
                mock.patch.object(validate_book, "REPO_ROOT", repo_root),
                mock.patch.object(validate_book, "DEFAULT_EPUB", epub_path),
                mock.patch.dict(os.environ, {"EPUBCHECK_JAR": str(jar_path)}, clear=True),
                mock.patch("scripts.validate_book.shutil.which", return_value="java"),
                mock.patch(
                    "scripts.validate_book.subprocess.run",
                    return_value=mock.Mock(returncode=0),
                ) as run_mock,
            ):
                validate_book.main()

        self.assertNotIn("shell", run_mock.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
