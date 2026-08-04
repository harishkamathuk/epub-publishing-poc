# EPUB Publishing POC

This repository is a disposable proof of concept for a local EPUB publishing workflow.
Its purpose is to prove that a manuscript-adjacent repository can build a selected set
of Markdown chapters into an EPUB without pulling planning or reference material into
the published book by accident.

## Repository structure

```text
drafts/     work-in-progress manuscript chapters
planning/   planning notes kept for repository compatibility
reference/  research notes kept for repository compatibility
book/       publication manifest, metadata, and EPUB styling
scripts/    Python build entry point
tests/      unit tests for the build script
.vscode/    shared editor task for local builds
dist/       generated build output
```

`book/chapters.txt` exists to define the authoritative publication order. Only files
listed there are passed to Pandoc, which means `planning/` and `reference/` are not
published unless they are explicitly added to the manifest.

## Prerequisites

- Python 3
- Pandoc

Check that both are available:

```bash
python --version
pandoc --version
```

## Unit tests

Run the built-in `unittest` suite from the repository root:

```bash
python -m unittest discover -s tests
```

## Build from the terminal

Build the EPUB from the repository root:

```bash
python scripts/build_book.py
```

The expected output location is:

```text
dist/epub-publishing-poc.epub
```

## Build from VS Code

Open the command palette, run `Tasks: Run Build Task`, and select `Build EPUB`.
The shared task runs:

```bash
python scripts/build_book.py
```

## Future phases

The following phases are planned, but they are not claimed as implemented here:

- EPUBCheck validation
- GitHub preview workflow
- PR validation
- Manual versioned release workflow
