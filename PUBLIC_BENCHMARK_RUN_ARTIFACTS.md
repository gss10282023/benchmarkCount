# External Public Benchmark Run Artifacts

This document is the canonical download map for public run artifacts used with
the repository's benchmark case packets. The repository deliberately does not
redistribute trajectories, screenshots, videos, container images, repository
checkouts, or leaderboard job archives. Download those artifacts directly from
the benchmark owners onto the scoring machine.

The original inventory was checked on 2026-07-18 and the DeepSWE v1.1 entry was
checked on 2026-07-19. Upstream repositories can change, so every formal
experiment must retain the pinned revision, the upstream object name or
job/trial ID, the byte size, and a locally computed SHA-256 manifest.

## Storage boundary

Use a directory outside the Git worktree, for example:

```bash
export PUBLIC_RUN_ROOT=/srv/benchmark-public-runs
mkdir -p "$PUBLIC_RUN_ROOT"
```

If an external directory is not available, `results/raw_runs/` is already
ignored by this repository. Never copy downloaded raw artifacts under
`experiments/case_packets/`.

After each download, record an immutable local inventory. On Linux:

```bash
find "$PUBLIC_RUN_ROOT" -type f -print0 \
  | sort -z \
  | xargs -0 sha256sum > "$PUBLIC_RUN_ROOT/SHA256SUMS"
```

Treat the case packet as the task/evaluator contract and the external archive
as run-specific evidence. Do not copy a trajectory into every task packet.

## OSWorld-Verified, no-Google-Drive split

- Canonical task split: `evaluation_examples/test_nogdrive.json` (361 tasks).
- Public run repository: [xlangai/ubuntu_osworld_verified_trajs](https://huggingface.co/datasets/xlangai/ubuntu_osworld_verified_trajs).
- Pinned artifact snapshot: `5124c991419d4c40deebab2c317735302c1cbdc0`.
- Pinned snapshot browser: [files at the pinned revision](https://huggingface.co/datasets/xlangai/ubuntu_osworld_verified_trajs/tree/5124c991419d4c40deebab2c317735302c1cbdc0).
- Join key: OSWorld task UUID from the packet and result directory/config.

Install the Hugging Face CLI and mirror the published ZIP run packages:

```bash
python -m pip install --upgrade 'huggingface_hub[cli]'
hf download xlangai/ubuntu_osworld_verified_trajs \
  --repo-type dataset \
  --revision 5124c991419d4c40deebab2c317735302c1cbdc0 \
  --include '*.zip' \
  --local-dir "$PUBLIC_RUN_ROOT/osworld_verified"
```

The snapshot contains many agent/model/step-budget packages rather than one
homogeneous cohort. Do not mix 15-, 50-, and 100-step runs in one comparison.
For a 361-task short-horizon reference cohort, one published package is
`claude-4-sonnet-20250514-50steps.zip`. Verify the 361 expected task UUIDs after
extraction; an archive being public does not by itself prove cohort
completeness.

## OSWorld 2.0

- Canonical benchmark release: [`osworld-v2-2026.06.24`](https://github.com/xlang-ai/OSWorld-V2/releases/tag/v2026.06.24) (108 tasks).
- Release manifest: [`benchmark_releases/osworld-v2-2026.06.24.json`](https://github.com/xlang-ai/OSWorld-V2/blob/v2026.06.24/benchmark_releases/osworld-v2-2026.06.24.json).
- Public run repository: [xlangai/osworld2.0-trajectory](https://huggingface.co/datasets/xlangai/osworld2.0-trajectory).
- Pinned artifact snapshot: `b2d4e7b9f2b842b64433c1af526b36c272d27fe6`.
- Pinned snapshot browser: [files at the pinned revision](https://huggingface.co/datasets/xlangai/osworld2.0-trajectory/tree/b2d4e7b9f2b842b64433c1af526b36c272d27fe6).
- Join key: OSWorld 2.0 task ID plus the pinned task-class hash.

Mirror only root-level run archives, excluding the duplicate website demo
tree:

```bash
python -m pip install --upgrade 'huggingface_hub[cli]'
hf download xlangai/osworld2.0-trajectory \
  --repo-type dataset \
  --revision b2d4e7b9f2b842b64433c1af526b36c272d27fe6 \
  --include '*.zip' \
  --exclude 'website_demo/**' \
  --local-dir "$PUBLIC_RUN_ROOT/osworld_2_0"
```

At the pinned snapshot, the root packages cover Claude Opus 4.7, Claude Sonnet
4.6, GPT-5.5, MiniMax M3, Qwen 3.7+, and GLM-v5-turbo configurations. A
published 108-task reference package is `results_opus4.7_500steps.zip`.
Preserve `trajectory`, `result`, `runtime`, checkpoint/evaluation logs and
screenshots when scoring; a result scalar alone is not sufficient evidence.

The official task classes are a separate gated dataset,
[xlangai/osworld_v2_tasks](https://huggingface.co/datasets/xlangai/osworld_v2_tasks),
released under Apache-2.0 but gated to reduce benchmark leakage. Accept its
access conditions and authenticate before locally materializing drafting
packets. Do not expose those task classes to the evaluated agent or use public
trajectory archives to bypass the gate.

## Terminal-Bench 2.1 verifier artifacts

- Canonical task source: [`terminal-bench/terminal-bench-2-1@6`](https://hub.harborframework.com/datasets/terminal-bench/terminal-bench-2-1/6) (89 tasks).
- Public result index: [Terminal-Bench 2.1 leaderboard](https://www.tbench.ai/leaderboard/terminal-bench/2.1).
- Download documentation: [Harbor job and trial downloads](https://www.harborframework.com/docs/sharing/jobs).
- Checked CLI: [Harbor 0.19.0 on PyPI](https://pypi.org/project/harbor/0.19.0/), including the pinned [`hub` command implementation](https://github.com/harbor-framework/harbor/blob/v0.19.0/src/harbor/cli/hub.py).
- Join key: `(task.name, task.digest)` from each packet and the run's
  `lock.json`; do not join by task name alone.

Pin the checked Harbor CLI and authenticate, even for public job downloads:

```bash
uv tool install 'harbor==0.19.0'
harbor auth login
```

If Harbor is already installed as a `uv` tool, run `uv tool upgrade harbor`
and confirm `harbor --version` is at least 0.19.0. Older 0.6.x releases used
the now-obsolete `harbor job ...` command shape and could not enumerate all
job trials.

Download the six jobs that expose whole-job archives:

```bash
for job_id in \
  f9d0318d-30f9-5d6f-bd7f-0ad5acf780d7 \
  ed9327d8-4601-5acb-a7a2-c71dfda0f5dc \
  e15e18db-c8c1-5e9f-9064-1d68975b3c91 \
  10e2e56b-ed31-5f65-a489-69f78b902adf \
  42cd19c9-42ad-5d79-b033-adf4f879423d \
  fd8707bb-51e8-56fa-8e46-769a82a531ae
do
  harbor hub job download "$job_id" \
    -o "$PUBLIC_RUN_ROOT/terminal_bench_2_1/jobs"
done
```

For the five jobs with no complete job archive, `job trials` automatically
paginates when `--page` is omitted; `--all-attempts` retains retries, and `-q`
prints only trial UUIDs. Enumerate all 2,330 IDs, remove the three
metadata-only failures listed below, and download the 2,327 available trial
archives:

```bash
harbor hub job trials \
  d478d2af-5348-575c-b20a-e5a2434dbff7 \
  a3019ec2-bc78-5ff6-9cae-d22d62470515 \
  84f460e2-f7f8-5249-8e63-d58b197968c7 \
  4860a28f-bc1a-5367-9885-57ff9ccc3a15 \
  36288ba6-447b-5161-babf-cb46a228436c --all-attempts -q \
  | sort -u \
  > "$PUBLIC_RUN_ROOT/terminal_bench_2_1/trial_ids_all.txt"

grep -Ev \
  '^(506d75fd-aa6c-5a44-b2e6-1ff54cb993e9|ae48f526-8fcb-5ae3-b4aa-548e320a1faf|969a4bf7-a739-5e48-bb53-965cc355ec50)$' \
  "$PUBLIC_RUN_ROOT/terminal_bench_2_1/trial_ids_all.txt" \
  > "$PUBLIC_RUN_ROOT/terminal_bench_2_1/trial_ids_downloadable.txt"

while IFS= read -r trial_id; do
  harbor hub trial download "$trial_id" \
    -o "$PUBLIC_RUN_ROOT/terminal_bench_2_1/trials"
done < "$PUBLIC_RUN_ROOT/terminal_bench_2_1/trial_ids_downloadable.txt"
```

The checked leaderboard had 17 agent/model rows backed by 11 unique public
jobs containing 8,105 trial records in total. Six jobs exposed whole-job
archives; the other five contained 2,330 trials, of which 2,327 exposed
individual trial archives. The three remaining failed trials had neither an
archive nor a trajectory object and must still remain in denominator/error
accounting. The de-duplicated download plan is 2,333 storage objects
(6 whole jobs plus 2,327 trials), totaling 4,985,215,051 compressed bytes
(4.985 GB / 4.643 GiB) at the checked snapshot. Preserve `config.json`,
`lock.json`, `result.json`, `agent/trajectory.json`, verifier outputs,
artifact manifests, logs and any exception records.

The three metadata-only failed trial IDs are
`506d75fd-aa6c-5a44-b2e6-1ff54cb993e9`,
`ae48f526-8fcb-5ae3-b4aa-548e320a1faf`, and
`969a4bf7-a739-5e48-bb53-965cc355ec50`. Record their failure metadata even
though Harbor has no corresponding archive object to download.

The exact leaderboard-to-job inventory checked on 2026-07-18 is below.
Leaderboard ID: `60330f75-0dd8-47ea-bd1d-e2ea28945731`; canonical row prefix:
`https://hub.harborframework.com/datasets/terminal-bench/terminal-bench-2-1/6/leaderboards/main/rows/`.
The row IDs are retained because several displayed agent/model rows share one
underlying job.

| Public Harbor job | Published row(s) | Download granularity |
|---|---|---|
| [`f9d0318d-30f9-5d6f-bd7f-0ad5acf780d7`](https://hub.harborframework.com/jobs/f9d0318d-30f9-5d6f-bd7f-0ad5acf780d7) | Claude Code / Fable 5 (`40dbe33d-e8af-475b-8eba-7d5d8f70054c`) | whole job |
| [`ed9327d8-4601-5acb-a7a2-c71dfda0f5dc`](https://hub.harborframework.com/jobs/ed9327d8-4601-5acb-a7a2-c71dfda0f5dc) | Terminus 2 / Fable 5 (`ce0677b9-0fea-46ce-b8de-893c4d68e77a`) | whole job |
| [`e15e18db-c8c1-5e9f-9064-1d68975b3c91`](https://hub.harborframework.com/jobs/e15e18db-c8c1-5e9f-9064-1d68975b3c91) | mini-SWE-agent / Muse Spark 1.1 (`64890377-54de-4cc2-bcd7-e76610983482`) | whole job |
| [`10e2e56b-ed31-5f65-a489-69f78b902adf`](https://hub.harborframework.com/jobs/10e2e56b-ed31-5f65-a489-69f78b902adf) | Codex / GPT-5.5 (`6d091468-3fda-4cbf-ba1c-645b0f522e97`); Terminus 2 / GPT-5.5 (`db1f499b-d948-43d2-9aaf-27cfe97f6caf`); Terminus 2 / Gemini 3 Pro (`b03a8a69-fea8-42dd-a4fb-96a6a39e6857`); Claude Code / Opus 4.7 (`fdb8393b-5b29-4645-b784-84f52cf31722`); Terminus 2 / Opus 4.7 (`f867b631-36c8-476e-aa2f-96007ae70da0`) | whole job |
| [`42cd19c9-42ad-5d79-b033-adf4f879423d`](https://hub.harborframework.com/jobs/42cd19c9-42ad-5d79-b033-adf4f879423d) | Gemini CLI / Gemini 3.1 Pro (`1095d399-9d66-44f4-8adc-e11fbb407a68`); Terminus 2 / Gemini 3.1 Pro (`360942d9-d27b-4f7e-bcf6-e0ea9cdcdee8`) | whole job |
| [`fd8707bb-51e8-56fa-8e46-769a82a531ae`](https://hub.harborframework.com/jobs/fd8707bb-51e8-56fa-8e46-769a82a531ae) | Gemini CLI / Gemini 3 Pro (`660c330f-9cd8-4ce7-8890-3ce573d038a0`); Claude Code / GLM-5.1 (`ef2b00eb-f360-41e6-8c97-23c4d762d06b`) | whole job |
| [`d478d2af-5348-575c-b20a-e5a2434dbff7`](https://hub.harborframework.com/jobs/d478d2af-5348-575c-b20a-e5a2434dbff7) | Cursor CLI / Grok 4.5 (`1fe87c62-99ed-477b-9f6c-23ffbabc49f6`) | individual trials only |
| [`a3019ec2-bc78-5ff6-9cae-d22d62470515`](https://hub.harborframework.com/jobs/a3019ec2-bc78-5ff6-9cae-d22d62470515) | Claude Code / Opus 4.8 (`dcd48d03-9df9-46ab-bc4c-ade6dc35b8da`) | individual trials only |
| [`84f460e2-f7f8-5249-8e63-d58b197968c7`](https://hub.harborframework.com/jobs/84f460e2-f7f8-5249-8e63-d58b197968c7) | Codex / GPT-5.6 Terra (`23ab6a14-4b2d-461d-9171-f8109f5692f1`) | individual trials only |
| [`4860a28f-bc1a-5367-9885-57ff9ccc3a15`](https://hub.harborframework.com/jobs/4860a28f-bc1a-5367-9885-57ff9ccc3a15) | Codex / GPT-5.6 Luna (`e5f3feda-4629-46ba-963f-300dcf7c2a4c`) | individual trials only |
| [`36288ba6-447b-5161-babf-cb46a228436c`](https://hub.harborframework.com/jobs/36288ba6-447b-5161-babf-cb46a228436c) | Claude Code / Sonnet 5 (`d7540f21-67af-4b3a-ad31-b81b85fef895`) | individual trials only |

The GitHub repository and Harbor revision 6 are not assumed byte-identical.
Leaderboard runs are bound to Harbor task digests; use the packet's stored
revision-6/per-task hashes when joining and regrading.

## DeepSWE v1.1

- Canonical task source: [datacurve-ai/deep-swe](https://github.com/datacurve-ai/deep-swe) at commit
  `3cda4081fed96103a6395de39c85e9b20275e307`; pinned `tasks/` tree
  `891e2975cd842071f62e567c3b11cae7362bf065` (113 tasks).
- Public data browser: [DeepSWE v1.1 trials](https://deepswe.datacurve.ai/data/v1.1/trials).
- Release manifest: [`release.json`](https://deepswe.datacurve.ai/artifacts/v1.1/release.json).
- Per-trial index: `https://deepswe.datacurve.ai/artifacts/v1.1/trials.json`.
- Artifact origin: `https://d3ujjcmjq6o8v6.cloudfront.net` with release prefix
  `v1.1/trial-artifacts`.
- Join key: task directory name from the packet and the index's exact
  `trial_name`; retain the model/configuration fields that define the rollout
  cohort.

The release manifest publishes these per-trial object patterns:

```text
v1.1/trial-artifacts/{trial_name}/agent/trajectory.json
v1.1/trial-artifacts/{trial_name}/artifacts/model.patch
v1.1/trial-artifacts/{trial_name}/agent/mini-swe-agent.txt
v1.1/trial-artifacts/{trial_name}/verifier/test-stdout.txt
v1.1/trial-artifacts/{trial_name}/verifier/{file}
```

The lifecycle boundary is mandatory: freeze every case packet and evidence
checklist before downloading or parsing `trials.json` or any per-trial object.
The release manifest may establish artifact *types* before the lock, but its
per-record values, trajectories, patches, verifier outputs, and released
labels must remain inaccessible to packet drafting and evidence scoring.

After the lock, download the trial index once, preserve its response metadata
and hash, select an explicitly declared rollout cohort, then mirror the object
paths supplied by the index/manifest into external storage. For example:

```bash
mkdir -p "$PUBLIC_RUN_ROOT/deep_swe_v1_1"
curl -fL \
  https://deepswe.datacurve.ai/artifacts/v1.1/trials.json \
  -o "$PUBLIC_RUN_ROOT/deep_swe_v1_1/trials.json"

# For each selected trial_name, expand and download every published object
# pattern. Preserve HTTP status for absent optional objects rather than
# silently dropping the trial from the cohort.
```

Keep the official released result/label as a retained post-lock field. First
produce the independent native evidence verdict (`S`, `F`, or `U`); only then
compare the two fields. A disagreement starts record-level review and is not,
by itself, a confirmed benchmark conflict. Do not copy trial names, model
patches, trajectory text, verifier outputs, or result values back into
`experiments/case_packets/deep_swe_v1_1/`.

## SWE-bench Pro

- Task dataset: [ScaleAI/SWE-bench_Pro](https://huggingface.co/datasets/ScaleAI/SWE-bench_Pro).
- Current packet dataset revision: `7ab5114912baf22bb098818e604c02fe7ad2c11f`.
- Current packet evaluator commit: `ca10a60a5fcae51e6948ffe1485d4153d421e6c5`.
- Historical trajectory-era dataset revision recorded by the root source lock:
  `9c13b199fe2d3195214e2f0c6bf3c7d6f81e3877`.
- Open-source harness and trajectory documentation: [scaleapi/SWE-bench_Pro-os](https://github.com/scaleapi/SWE-bench_Pro-os/tree/main/traj).
- Public raw artifact root: `s3://scaleapi-results/swe-bench-pro/`.
- Public object listing: [S3 prefix listing](https://scaleapi-results.s3.amazonaws.com/?list-type=2&prefix=swe-bench-pro/&delimiter=/).
- Browser-based trajectory viewer: [Docent SWE-bench Pro dashboard](https://docent.transluce.org/dashboard/032fb63d-4992-4bfc-911d-3b7dafcb931f).
- Join key: dataset `instance_id` and exact S3 run prefix.

Per-case case packets deliberately exclude public-run model names, trajectory
pointers, patches, and evaluator-output URLs. Keep acquisition and historical
contract metadata in this document and in the packet corpus root
`source_lock.json`; join those external artifacts only after checklist drafting.

The official instructions describe an AWS account and configured AWS CLI. The
bucket also currently accepts anonymous public reads; use `--no-sign-request`
when no account is configured. List the available run prefixes before choosing
a cohort:

```bash
aws s3 ls s3://scaleapi-results/swe-bench-pro/ --no-sign-request
```

The pinned external inventory currently has these 15 run prefixes:

```text
claude-45haiku-10222025
claude-45sonnet-10132025
claude-4sonnet-10132025
claude-opus-4-1-paper
claude-sonnet-4-paper
gemini-2-5-pro-preview-250-turns-debug-nov17
gemini-2-5-pro-preview-250-turns-debug-oct22
gemini-2-5-pro-preview-paper
glm-4p5-10222025
gpt-4o-paper
gpt-5-250-turns-10132025
gpt-5-codex-debug-oct22
gpt-5-high-paper
gptoss-paper
kimi-paper
```

Mirror all currently published run artifacts, or replace the final source with
one selected prefix:

```bash
aws s3 sync s3://scaleapi-results/swe-bench-pro/ \
  "$PUBLIC_RUN_ROOT/swe_bench_pro/" \
  --no-sign-request

# Example single configuration:
aws s3 sync \
  s3://scaleapi-results/swe-bench-pro/claude-45sonnet-10132025/ \
  "$PUBLIC_RUN_ROOT/swe_bench_pro/claude-45sonnet-10132025/" \
  --no-sign-request
```

The public historical full-run cohorts contain 730 trajectories for a
731-instance dataset; retain the missing-instance record explicitly rather
than silently changing the denominator. The date-named runs use a 250-turn,
no-cost-limit configuration, while `paper` runs use a different cost contract.
Do not combine those configurations.

The public trajectories were produced against historical task/test contracts.
When scoring with the current packets, report two distinct fields:

- `historical_official_reward`: the reward shipped with the public run under
  its original contract.
- `recomputed_reward`: a new verifier result under the packet's explicitly
  pinned current contract.

Never overwrite one with the other. Preserve each S3 key, ETag, byte size and
last-modified timestamp in the VPS-side inventory.

## Paper and release wording

The paper and released repository should state that case packets and derived
checklists are distributed, while raw third-party run artifacts remain hosted
by their benchmark owners and must be downloaded from the pinned locations in
this document. Public availability is not a grant to relicense or republish an
upstream artifact; users remain responsible for the applicable dataset terms,
licenses and access controls.
