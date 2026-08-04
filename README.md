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
scripts/    Python entry points for local build and validation
tests/      unit tests for the build and validation scripts
.vscode/    shared editor task for local builds
dist/       generated build output
```

`book/chapters.txt` exists to define the authoritative publication order. Only files
listed there are passed to Pandoc, which means `planning/` and `reference/` are not
published unless they are explicitly added to the manifest.

## Prerequisites

- Python 3
- Pandoc
- EPUBCheck JAR

Check the core tools first:

```bash
python --version
pandoc --version
```

### EPUBCheck JAR setup

Set `EPUBCHECK_JAR` to the EPUBCheck JAR file and ensure Java is available on
`PATH`.

PowerShell example:

```powershell
$env:EPUBCHECK_JAR = 'C:\path\to\epubcheck.jar'
java -version
```

In this mode, `python scripts/validate_book.py` will run:

```text
java -jar <EPUBCHECK_JAR> dist/epub-publishing-poc.epub
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

Successful EPUB creation means the package was built. It does not, by itself,
mean the EPUB conforms to the standard.

## Validate from the terminal

Validate the default EPUB with EPUBCheck:

```bash
python scripts/validate_book.py
```

This validates the fixed default EPUB:

```text
dist/epub-publishing-poc.epub
```

To build and then validate from the terminal:

```bash
python scripts/build_book.py
python scripts/validate_book.py
```

Successful EPUB conformance validation means EPUBCheck completed without errors.
It does not perform editorial review, spell-checking, or visual reader testing.

## Build from VS Code

Open the command palette, run `Tasks: Run Build Task`, and use the default build
task `Build and Validate EPUB`.

The shared tasks run:

```bash
python scripts/build_book.py
python scripts/validate_book.py
```

## Future phases

The following phases are planned, but they are not claimed as implemented here:

- GitHub preview workflow
- PR validation
- Manual versioned release workflow
