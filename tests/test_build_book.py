from __future__ import annotations

import argparse
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import build_book


class LoadChaptersTests(unittest.TestCase):
    def test_load_chapters_ignores_comments_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            chapter_one = repo_root / "drafts" / "chapter-01.md"
            chapter_two = repo_root / "drafts" / "chapter-02.md"
            manifest = repo_root / "book" / "chapters.txt"

            chapter_one.parent.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            chapter_one.write_text("# One\n", encoding="utf-8")
            chapter_two.write_text("# Two\n", encoding="utf-8")
            manifest.write_text(
                "\n# comment\ndrafts/chapter-01.md\n\ndrafts/chapter-02.md\n",
                encoding="utf-8",
            )

            with mock.patch.object(build_book, "REPO_ROOT", repo_root):
                chapters = build_book.load_chapters(manifest)

            self.assertEqual(chapters, [chapter_one, chapter_two])

    def test_load_chapters_rejects_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            manifest = repo_root / "book" / "chapters.txt"

            with mock.patch.object(build_book, "REPO_ROOT", repo_root):
                with self.assertRaisesRegex(FileNotFoundError, "Missing chapters manifest"):
                    build_book.load_chapters(manifest)

    def test_load_chapters_requires_at_least_one_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            manifest = repo_root / "book" / "chapters.txt"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("# comment only\n", encoding="utf-8")

            with mock.patch.object(build_book, "REPO_ROOT", repo_root):
                with self.assertRaisesRegex(ValueError, "No chapters found"):
                    build_book.load_chapters(manifest)

    def test_load_chapters_rejects_missing_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            manifest = repo_root / "book" / "chapters.txt"

            manifest.parent.mkdir(parents=True)
            manifest.write_text("drafts/missing-chapter.md\n", encoding="utf-8")

            with mock.patch.object(build_book, "REPO_ROOT", repo_root):
                with self.assertRaisesRegex(
                    FileNotFoundError,
                    "Chapter listed in manifest does not exist",
                ):
                    build_book.load_chapters(manifest)

    def test_load_chapters_rejects_non_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            chapter = repo_root / "drafts" / "chapter-01.txt"
            manifest = repo_root / "book" / "chapters.txt"

            chapter.parent.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            chapter.write_text("plain text\n", encoding="utf-8")
            manifest.write_text("drafts/chapter-01.txt\n", encoding="utf-8")

            with mock.patch.object(build_book, "REPO_ROOT", repo_root):
                with self.assertRaisesRegex(ValueError, "is not a Markdown file"):
                    build_book.load_chapters(manifest)

    def test_load_chapters_rejects_paths_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            outside = repo_root.parent / "outside.md"
            manifest = repo_root / "book" / "chapters.txt"

            manifest.parent.mkdir(parents=True)
            outside.write_text("# Outside\n", encoding="utf-8")
            manifest.write_text("../outside.md\n", encoding="utf-8")

            with mock.patch.object(build_book, "REPO_ROOT", repo_root):
                with self.assertRaisesRegex(ValueError, "outside the repository"):
                    build_book.load_chapters(manifest)


class BuildCommandTests(unittest.TestCase):
    def test_build_command_uses_manifest_order_and_epub3(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            book_dir = repo_root / "book"
            metadata = book_dir / "metadata.yaml"
            css = book_dir / "epub.css"
            chapter_two = repo_root / "drafts" / "chapter-02.md"
            chapter_one = repo_root / "drafts" / "chapter-01.md"
            output = repo_root / "dist" / "book.epub"

            metadata.parent.mkdir(parents=True)
            chapter_one.parent.mkdir(parents=True)
            metadata.write_text("---\ntitle: Test\n...\n", encoding="utf-8")
            css.write_text("body { font-family: serif; }\n", encoding="utf-8")
            chapter_one.write_text("# One\n", encoding="utf-8")
            chapter_two.write_text("# Two\n", encoding="utf-8")

            with (
                mock.patch.object(build_book, "REPO_ROOT", repo_root),
                mock.patch.object(build_book, "BOOK_DIR", book_dir),
                mock.patch.object(build_book, "METADATA_PATH", metadata),
                mock.patch.object(build_book, "CSS_PATH", css),
                mock.patch("scripts.build_book.shutil.which", return_value="pandoc"),
            ):
                command = build_book.build_command(
                    [chapter_two, chapter_one],
                    output,
                )

            self.assertEqual(command[0:5], ["pandoc", "--from", "gfm", "--to", "epub3"])
            self.assertIn("--metadata-file", command)
            self.assertIn("--css", command)
            self.assertIn("--toc", command)
            self.assertIn("--standalone", command)
            self.assertEqual(command[-2:], [str(chapter_two), str(chapter_one)])


class MainTests(unittest.TestCase):
    def test_main_returns_error_when_pandoc_is_missing(self) -> None:
        with mock.patch.object(
            build_book,
            "parse_args",
            return_value=argparse.Namespace(
                manifest=Path("book/chapters.txt"),
                output=Path("dist/epub-publishing-poc.epub"),
            ),
        ), mock.patch("scripts.build_book.shutil.which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "Pandoc is not installed"):
                build_book.main()

    def test_parse_args_defaults_match_contract(self) -> None:
        args = build_book.parse_args([])
        self.assertEqual(args.manifest, build_book.DEFAULT_MANIFEST)
        self.assertEqual(args.output, build_book.DEFAULT_OUTPUT)

    def test_main_prints_status_and_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            manifest = repo_root / "book" / "chapters.txt"
            metadata = repo_root / "book" / "metadata.yaml"
            css = repo_root / "book" / "epub.css"
            chapter = repo_root / "drafts" / "chapter-01.md"
            output = repo_root / "dist" / "epub-publishing-poc.epub"

            manifest.parent.mkdir(parents=True)
            chapter.parent.mkdir(parents=True)
            manifest.write_text("drafts/chapter-01.md\n", encoding="utf-8")
            metadata.write_text("---\ntitle: Test\n...\n", encoding="utf-8")
            css.write_text("body { font-family: serif; }\n", encoding="utf-8")
            chapter.write_text("# One\n", encoding="utf-8")

            stdout = io.StringIO()

            with (
                mock.patch.object(build_book, "REPO_ROOT", repo_root),
                mock.patch.object(build_book, "BOOK_DIR", repo_root / "book"),
                mock.patch.object(build_book, "DIST_DIR", repo_root / "dist"),
                mock.patch.object(build_book, "DEFAULT_MANIFEST", manifest),
                mock.patch.object(build_book, "DEFAULT_OUTPUT", output),
                mock.patch.object(build_book, "METADATA_PATH", metadata),
                mock.patch.object(build_book, "CSS_PATH", css),
                mock.patch.object(
                    build_book,
                    "parse_args",
                    return_value=argparse.Namespace(
                        manifest=Path("book/chapters.txt"),
                        output=Path("dist/epub-publishing-poc.epub"),
                    ),
                ),
                mock.patch("scripts.build_book.shutil.which", return_value="pandoc"),
                mock.patch("scripts.build_book.subprocess.run", return_value=mock.Mock(returncode=0)),
                contextlib.redirect_stdout(stdout),
            ):
                result = build_book.main()

            output_text = stdout.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("Including chapters:", output_text)
            self.assertIn("drafts/chapter-01.md", output_text.replace("\\", "/"))
            self.assertIn(f"Output path: {output}", output_text)
            self.assertIn("EPUB build completed successfully.", output_text)


if __name__ == "__main__":
    unittest.main()
