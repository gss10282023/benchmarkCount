# Revised Agent Benchmark Paper Package

The two supplied v2 paper snapshots are kept separately under [`paper/`](paper/):

- `paper/v2_blue_annotated/` — the current revision with blue
  `\paperupdate` annotations.
- `paper/v2_zip_snapshot/` — the version imported from the supplied ZIP.

Each snapshot is self-contained and includes its own editable `main.tex`,
bibliography, NeurIPS style, and figures. The blue-annotated snapshot also
retains its rendered `main.pdf`; the ZIP snapshot retains the byte-exact input
archive. See [`paper/README.md`](paper/README.md) for provenance and SHA-256
hashes.

Benchmark reproducibility assets:

- [`experiments/case_packets/README.md`](experiments/case_packets/README.md) —
  generated task/evaluator packet corpora and rebuild/draft commands.
- [`PUBLIC_BENCHMARK_RUN_ARTIFACTS.md`](PUBLIC_BENCHMARK_RUN_ARTIFACTS.md) —
  owner-hosted raw-run download locations for VPS-side scoring. Raw third-party
  trajectories and run archives are intentionally not redistributed here.

To rebuild either PDF locally, enter the selected snapshot and run:

```sh
latexmk -pdf -interaction=nonstopmode main.tex
```

On Overleaf, upload the contents of one snapshot folder and set `main.tex` as
the main file. Do not merge the two snapshots implicitly.
