from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EPUB = REPO_ROOT / "dist" / "epub-publishing-poc.epub"


def main() -> int:
    epub_path = DEFAULT_EPUB
    if not epub_path.exists():
        print(f"EPUB file is missing: {epub_path}", file=sys.stderr)
        return 1

    epubcheck_jar = os.environ.get("EPUBCHECK_JAR")
    if not epubcheck_jar:
        print("EPUBCHECK_JAR is not set.", file=sys.stderr)
        return 1

    jar_path = Path(epubcheck_jar).expanduser().resolve()
    if not jar_path.exists():
        print(f"EPUBCheck JAR is missing: {jar_path}", file=sys.stderr)
        return 1
    if not jar_path.is_file():
        print(f"EPUBCheck JAR is not a file: {jar_path}", file=sys.stderr)
        return 1

    java_binary = shutil.which("java")
    if java_binary is None:
        print("Java is not available on PATH.", file=sys.stderr)
        return 1

    command = [java_binary, "-jar", str(jar_path), str(epub_path)]
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
