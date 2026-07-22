# AgentDojo v1.2.2 full-coverage extension

This directory is an isolated, pre-run appendix experiment. It does not replace
or mutate the repository's existing 100-case main experiment.

## Locked definition

- AgentDojo distribution: `0.1.35`
- official tag / commit: `v0.1.35` / `a75aba7631d3ca5fb7ab938965c97ead2f9ff84b`
- benchmark: `v1.2.2`
- attack / defense: `direct` / `None`
- tool delimiter / output format: `tool` / `yaml`
- effective default system-message SHA-256:
  `a021a92b114c523250d0e52b18adc0aa7b41db7c7628b579b2b8db1df9361837`
- result namespace: `agentdojo_full_v1.2.2_direct`
- install extra: `agentdojo-full` (`agentdojo==0.1.35` in `pyproject.toml`
  and the checked-in `uv.lock`)
- agents and model parameters: embedded in `lock/experiment_lock.json` and
  bound to the exact SHA-256 of `configs/agents.yaml`

The manifest is intentionally `draft`. The paper's existing 100 draft directories
are preserved byte-for-byte; the remaining 849 case packets have been repaired but
their checklists have not been drafted, reviewed, or locked. No formal benchmark
episode was executed by the packet-repair workflow.

## Rebuild sequence

Run from the repository root. Replace the checkout path with a clean official
AgentDojo `v0.1.35` checkout.

```bash
uv sync --extra dev --extra agentdojo-full --locked
```

```bash
.venv/bin/python -m evidence_system.cli.build_agentdojo_full_catalog \
  --paired-candidates experiments/official_splits/agentdojo_v1.2.2_paired_candidates.json \
  --output experiments/agentdojo_full_v1.2.2_direct/official_splits/agentdojo_selected_task_sources.json \
  --agentdojo-repo /path/to/agentdojo-v0.1.35 \
  --json

.venv/bin/python -m evidence_system.cli.prepare_agentdojo_full_experiment \
  --skip-lock \
  --created-at 2026-07-16T11:30:00+10:00 \
  --json

.venv/bin/python -m evidence_system.cli.build_case_packets \
  --manifest experiments/agentdojo_full_v1.2.2_direct/experiment_manifest.yaml \
  --official-splits experiments/agentdojo_full_v1.2.2_direct/official_splits \
  --output-root experiments/agentdojo_full_v1.2.2_direct/case_packets \
  --source-mode local \
  --json

.venv/bin/python -m evidence_system.cli.build_case_packet_source_bundle \
  --allow-generated-contract-ids \
  --json

.venv/bin/python -m evidence_system.cli.prepare_agentdojo_full_experiment \
  --skip-lock \
  --created-at 2026-07-16T11:30:00+10:00 \
  --json

.venv/bin/python -m evidence_system.cli.prepare_agentdojo_full_experiment \
  --locked-at 2026-07-16T11:30:00+10:00 \
  --json

.venv/bin/python -m evidence_system.cli.verify_agentdojo_full_experiment --json
```

The packet builder deletes and rebuilds an existing single-case directory. The
explicit full-coverage `--output-root` above is therefore mandatory.
For the pinned full catalog, local mode now materializes the official
evidence-relevant task/evaluator/state source closure plus outcome-free native
wiring and artifact inventories. A partial repair must pass the exact intended
`--case-unit-id` set; do not run the unfiltered command when the original 100
packet directories are under preservation.
The second manifest preparation records the finalized bundle hash. To avoid an
impossible manifest/bundle hash cycle, the bundle records a canonical manifest
definition hash with only `source_bundle_hash` excluded; the experiment lock
separately binds the exact manifest and bundle file hashes.

## Plan-only command

The repository's legacy `results/jobs/full` snapshot is protected by the macOS
`uchg` flag, so full-coverage job plans are kept inside this experiment root.
Actual adapter results remain isolated below
`results/namespaces/agentdojo_full_v1.2.2_direct/`.

```bash
.venv/bin/python -m evidence_system.cli.run_full \
  --domain agentdojo \
  --phase full \
  --experiment-type appendix \
  --manifest experiments/agentdojo_full_v1.2.2_direct/experiment_manifest.yaml \
  --source-bundle experiments/agentdojo_full_v1.2.2_direct/source_bundles/case_packet_source_bundle.json \
  --contracts-dir experiments/agentdojo_full_v1.2.2_direct/evidence_contracts/drafts \
  --infra-config configs/infra.yaml \
  --agents-config configs/agents.yaml \
  --jobs-dir experiments/agentdojo_full_v1.2.2_direct/jobs/full \
  --plan-only \
  --json
```

Omitting `--case-count` selects all 949 manifest cases. Omitting
`--experiment-type` infers `appendix`; an explicit value must match the
manifest. Planning verifies the experiment lock before writing any job. The
completed plan has 949 jobs for each of Agent A, B, and C (2,847 record slots).

## Acceptance gate

`provenance/acceptance_report.json` is accepted only when all of the following
are exact:

- 949 unique catalog, manifest, packet, and source-bundle case IDs in the same order;
- suite counts: workspace 560, travel 140, banking 144, slack 105;
- 949 `case_packet.md` and 949 `raw_case_manifest.json` files;
- all 1,898 source-bundle packet/manifest hashes and all 949 raw-case file hashes;
- 2,847 planned record slots and three scores per case;
- the exact 949 x 3 case/agent job Cartesian product, namespace, phase, and
  manifest hash for all 2,847 plan-only job files;
- locked package, tag, commit, attack, defense, tools, prompt, model, infra,
  source metadata, and runtime-code hashes;
- remote AgentDojo package version plus the pinned commit-derived source-file
  hashes relevant to every executed case;
- unchanged legacy 100-case source metadata, packet tree, and result tree.

Any mismatch is fail-closed and does not overwrite the last accepted report or
source bundle.
