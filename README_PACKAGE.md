# Revised Agent Benchmark Paper Package

Main editable source:
- `revised_agent_benchmark_paper.tex`

Current rendered PDF:
- `revised_agent_benchmark_paper.pdf`

Included local dependencies:
- `neurips_2026.sty`
- `ref.bib`
- `checklist.tex`
- `figures/`
- `revised_agent_benchmark_paper.bbl`

Benchmark reproducibility assets:

- [`experiments/case_packets/README.md`](experiments/case_packets/README.md) —
  generated task/evaluator packet corpora and rebuild/draft commands.
- [`PUBLIC_BENCHMARK_RUN_ARTIFACTS.md`](PUBLIC_BENCHMARK_RUN_ARTIFACTS.md) —
  owner-hosted raw-run download locations for VPS-side scoring. Raw third-party
  trajectories and run archives are intentionally not redistributed here.

To rebuild the PDF locally, run:

```sh
latexmk -pdf -interaction=nonstopmode revised_agent_benchmark_paper.tex
```

On Overleaf, upload the contents of this folder and set
`revised_agent_benchmark_paper.tex` as the main file.
