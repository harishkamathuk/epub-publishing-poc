# EPUB Publishing POC

- This repository is an EPUB publishing proof of concept.
- `drafts/`, `planning/`, and `reference/` are retained for compatibility with the future real repository.
- `book/chapters.txt` is the authoritative publication manifest.
- Only manifest-listed files enter the book.
- Local and CI builds must call the same Python build script.
- Publication must eventually be explicit rather than triggered by every manuscript commit.
- Preview artefacts and published release assets are different concepts.
- Do not create tags or GitHub Releases until the final build has passed validation.
- Make changes in small, reviewable phases.
