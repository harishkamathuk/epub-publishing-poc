from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK_DIR = REPO_ROOT / "book"
DIST_DIR = REPO_ROOT / "dist"
DEFAULT_MANIFEST = BOOK_DIR / "chapters.txt"
DEFAULT_OUTPUT = DIST_DIR / "epub-publishing-poc.epub"
METADATA_PATH = BOOK_DIR / "metadata.yaml"
CSS_PATH = BOOK_DIR / "epub.css"
MARKDOWN_SUFFIXES = {".md", ".markdown"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the proof-of-concept EPUB.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Chapter manifest path. Defaults to book/chapters.txt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output EPUB path. Defaults to dist/epub-publishing-poc.epub",
    )
    return parser.parse_args(argv)


def resolve_repo_path(path: Path) -> Path:
    candidate = path if path.is_absolute() else REPO_ROOT / path
    return candidate.resolve()


def ensure_repo_relative(path: Path, description: str) -> Path:
    try:
        path.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"{description} resolves outside the repository: {path}") from exc
    return path


def load_chapters(chapters_file: Path) -> list[Path]:
    if not chapters_file.exists():
        raise FileNotFoundError(f"Missing chapters manifest: {chapters_file}")

    ensure_repo_relative(chapters_file, "Manifest")

    chapters: list[Path] = []
    for line_number, raw_line in enumerate(
        chapters_file.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        stripped = raw_line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue

        manifest_entry = raw_line.strip()
        chapter_path = ensure_repo_relative(
            resolve_repo_path(Path(manifest_entry)),
            f"Manifest entry on line {line_number}",
        )
        if not chapter_path.exists():
            raise FileNotFoundError(
                f"Chapter listed in manifest does not exist: {manifest_entry}"
            )
        if chapter_path.suffix.lower() not in MARKDOWN_SUFFIXES:
            raise ValueError(
                f"Chapter listed in manifest is not a Markdown file: {manifest_entry}"
            )
        chapters.append(chapter_path)

    if not chapters:
        raise ValueError(f"No chapters found in manifest: {chapters_file}")

    return chapters


def build_command(chapters: list[Path], output_path: Path) -> list[str]:
    pandoc_binary = shutil.which("pandoc")
    if pandoc_binary is None:
        raise FileNotFoundError("Pandoc is not installed or not on PATH.")

    cover_path = BOOK_DIR / "assets" / "cover.png"

    for required in (METADATA_PATH, CSS_PATH):
        if not required.exists():
            raise FileNotFoundError(f"Required build file is missing: {required}")

    command = [
        pandoc_binary,
        "--from",
        "gfm",
        "--to",
        "epub3",
        "--metadata-file",
        str(METADATA_PATH),
        "--css",
        str(CSS_PATH),
        "--toc",
        "--standalone",
        "--resource-path",
        str(REPO_ROOT),
        "--output",
        str(output_path),
    ]

    if cover_path.exists():
        command.extend(["--epub-cover-image", str(cover_path)])

    command.extend(str(chapter) for chapter in chapters)
    return command


def main() -> int:
    args = parse_args()
    manifest_path = resolve_repo_path(args.manifest)
    output_path = resolve_repo_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chapters = load_chapters(manifest_path)
    command = build_command(chapters, output_path)

    print("Including chapters:")
    for chapter in chapters:
        print(f"- {chapter.relative_to(REPO_ROOT)}")
    print(f"Output path: {output_path}")

    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    if completed.returncode != 0:
        return completed.returncode

    print("EPUB build completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
