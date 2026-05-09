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
- `outputs/latex/results_macros.tex`

Editable result placeholders:
- `outputs/latex/results_macros.tex` defines the current paper macros for
  tables and Figure 1. Replace `\fillfromdata` and draft numeric plot values
  with final scored-manifest values when available.

To rebuild the PDF locally, run:

```sh
latexmk -pdf -interaction=nonstopmode revised_agent_benchmark_paper.tex
```

On Overleaf, upload the contents of this folder and set
`revised_agent_benchmark_paper.tex` as the main file.
