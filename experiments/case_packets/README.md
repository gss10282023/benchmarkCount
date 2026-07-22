# Case-packet corpora

Each immediate child directory is one benchmark corpus. A task directory
contains the model-visible `agent_input.json`, controller/reviewer
`case_packet.json`, drafter input `case_packet.md`, provenance
`raw_case_manifest.json`, and any compact source files under `raw_case/`.

Raw model runs, screenshots, videos, repository checkouts, VM/container images
and leaderboard job archives are intentionally excluded. See
[`PUBLIC_BENCHMARK_RUN_ARTIFACTS.md`](../../PUBLIC_BENCHMARK_RUN_ARTIFACTS.md)
for their owner-hosted locations and VPS download commands.

## Added benchmark roots

| Packet root | Frozen task source | Expected cases | Local status |
|---|---|---:|---|
| `osworld_verified/` | OSWorld commit `87df18ff0e906dafdb1ea96b8299f35ec1e67e6b`, `test_nogdrive` | 361 | ready |
| `terminal_bench_2_1/` | Harbor `terminal-bench/terminal-bench-2-1@6` | 89 | ready |
| `deep_swe_v1_1/` | DeepSWE Git commit `3cda4081fed96103a6395de39c85e9b20275e307`, task tree `891e2975cd842071f62e567c3b11cae7362bf065` | 113 | ready |
| `swe_bench_pro/` | HF revision `7ab5114912baf22bb098818e604c02fe7ad2c11f` | 731 | ready |
| `osworld_2_0/` | release `osworld-v2-2026.06.24` and gated task tag `v2026.06.24` | 108 | ready; controller pointers only, gated code excluded |

`osworld_2_0/` contains all 108 draftable task directories. The official gated
implementation is not reconstructed from public trajectories and is never
copied into a packet. Eight official instructions contain controller-time
values; the static extractor preserves those as explicit website-host or
temporary Overleaf/GitLab credential placeholders without importing or
executing the gated task modules. Task `069` is multi-phase: its initial
`agent_input.json` contains phase 1 only, while its controller-only packet lists
all four instructions, weights, gates, and sequential-delivery boundary.

## Rebuild and verify

OSWorld-Verified can be rebuilt directly from its immutable public Git source:

```bash
python3 scripts/build_osworld_case_packets.py \
  --benchmark osworld_verified \
  --replace

python3 scripts/build_osworld_case_packets.py \
  --benchmark osworld_verified \
  --verify-only
```

Terminal-Bench packets are generated from a Harbor revision-6 source snapshot.
The builder verifies all 89 Harbor task package digests before writing. Packet
schema v2 also locks the native/stronger split, independent `S`/`F`/`U`
evidence verdict, post-score label comparison, and type-only artifact inventory:

```bash
harbor download terminal-bench/terminal-bench-2-1@6 \
  --output-dir /srv/benchmark-sources/terminal-bench-2-1

python3 scripts/build_terminal_bench_2_1_case_packets.py \
  --source-dir /srv/benchmark-sources/terminal-bench-2-1 \
  --output-root experiments/case_packets/terminal_bench_2_1

python3 scripts/build_terminal_bench_2_1_case_packets.py \
  --validate-only \
    --output-root experiments/case_packets/terminal_bench_2_1
```

DeepSWE v1.1 packets are generated only from the pinned official Git task
tree. The builder does not read the public trial index, trajectories, patches,
verifier results, or released labels. It retains every non-solution official
source byte and binds the excluded reference-solution bytes by path, size, and
SHA-256:

```bash
git clone https://github.com/datacurve-ai/deep-swe \
  /srv/benchmark-sources/deep-swe
git -C /srv/benchmark-sources/deep-swe checkout \
  3cda4081fed96103a6395de39c85e9b20275e307

python3 scripts/build_deep_swe_v1_1_case_packets.py \
  --source-dir /srv/benchmark-sources/deep-swe \
  --output-root experiments/case_packets/deep_swe_v1_1

python3 scripts/build_deep_swe_v1_1_case_packets.py \
  --validate-only \
  --output-root experiments/case_packets/deep_swe_v1_1
```

The byte-level two-benchmark fidelity audit is reproducible with:

```bash
python3 \
  audits/terminal_bench_2_1_deep_swe_v1_1_case_packets_20260719/audit_case_packets.py \
  --terminal-source-dir /srv/benchmark-sources/terminal-bench-2-1 \
  --deep-source-dir /srv/benchmark-sources/deep-swe
```

The checked 202-case result and audit boundary are documented in
[`audits/terminal_bench_2_1_deep_swe_v1_1_case_packets_20260719/README.md`](../../audits/terminal_bench_2_1_deep_swe_v1_1_case_packets_20260719/README.md).

SWE-bench Pro can be rebuilt from the pinned HF row corpus. The builder fails
closed if the upstream head or 731-row canonical digest has changed:

```bash
python3 scripts/build_swe_bench_pro_case_packets.py
python3 scripts/build_swe_bench_pro_case_packets.py --validate-only
```

To materialize OSWorld 2.0, first accept the official gated dataset terms and
download the pinned task files outside the repository:

```bash
hf auth login
hf download xlangai/osworld_v2_tasks \
  --repo-type dataset \
  --revision v2026.06.24 \
  --include 'task_*.py' 'manifests/task_hashes.json' \
  --local-dir /srv/benchmark-sources/osworld-v2-tasks

python3 scripts/build_osworld_case_packets.py \
  --benchmark osworld_2_0 \
  --osworld2-task-root /srv/benchmark-sources/osworld-v2-tasks \
  --osworld2-hash-manifest \
    /srv/benchmark-sources/osworld-v2-tasks/manifests/task_hashes.json \
  --replace
```

The builder checks the release-level task-hash manifest and all 108 task-file
hashes, then extracts only the agent-visible static-expression subset through
a restricted AST interpreter without importing or executing gated task code.
Hash- and AST-locked rules cover the eight runtime-template tasks and the one
multi-phase delivery contract. The task/evaluator implementation remains an
external controller source.

## Draft discovery

Use one benchmark root per batch. A dry run performs discovery and lane sizing
without invoking an LLM:

```bash
.venv/bin/python neurips_ed_track_minimal/scripts/run_draft_batch.py \
  --case-packet-root experiments/case_packets/terminal_bench_2_1 \
  --output-root results/drafts/terminal_bench_2_1 \
  --dry-run
```

Replace the packet/output roots for `osworld_verified`, `osworld_2_0`,
`deep_swe_v1_1`, or `swe_bench_pro`.

To preflight every locally ready corpus in one pass:

```bash
for benchmark in osworld_verified osworld_2_0 terminal_bench_2_1 deep_swe_v1_1 swe_bench_pro; do
  .venv/bin/python neurips_ed_track_minimal/scripts/run_draft_batch.py \
    --case-packet-root "experiments/case_packets/$benchmark" \
    --output-root "results/drafts/$benchmark" \
    --dry-run
done
```

Remove `--dry-run` only when the intended draft provider/model configuration is
active.

The tested agent must receive only `agent_input.json`. `case_packet.md`,
`case_packet.json`, `raw_case/`, tests, evaluator expectations and controller
metadata are drafting/scoring inputs and must never be added to the evaluated
agent's prompt or workspace.
