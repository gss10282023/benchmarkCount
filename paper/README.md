# Paper versions

This directory keeps the two supplied v2 paper snapshots separate. They are
not interchangeable and should not be overwritten or merged without an
explicit comparison.

## `v2_blue_annotated`

- Source: the paper directory that was present at the repository root before
  the 2026-07-23 reorganization.
- Distinguishing feature: `main.tex` contains 25 `\paperupdate` markers and
  defines the blue revision style.
- `main.tex` SHA-256:
  `106e057825ab8f12bfb4cbc1accf0c3a9de13ee61f87a8a074a3a887a2d44dd7`
- The rendered `main.pdf` is retained. Transient LaTeX/latexmk intermediates
  are intentionally excluded and can be regenerated from `main.tex`.

## `v2_zip_snapshot`

- Source: `/Users/gss/Downloads/Can_Agent_Benchmarks_Support_Their_Scores_ (1).zip`.
- Imported: 2026-07-23.
- Distinguishing feature: `main.tex` contains no `\paperupdate` markers.
- `main.tex` SHA-256:
  `1e17fa37ec4a27dceeeaad778de41f559f09cadc01c3a1c8f35c8324762bcd93`
- The byte-exact input archive is retained as `source_archive.zip`.
- `source_archive.zip` SHA-256:
  `c7e66b7bd69ec739e1ac3fc8c21b693543b587010dd11f073a0c42eef07c8d2d`
