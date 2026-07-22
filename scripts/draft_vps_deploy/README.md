# Draft + Score VPS deployment

This deployment exposes checklist drafting over SSH without opening a public HTTP
endpoint. Each case is generated through the same frozen draft prompt and schema as
the local package, using Codex login authentication, `gpt-5.4`, `xhigh`, output
verbosity of `medium`, an ephemeral session, and a read-only sandbox.

The remote layout is:

- `/opt/neurips-draft/app` — root-owned application snapshot
- `/opt/neurips-draft/venv` — Python environment
- `/srv/neurips-draft/home/.codex` — private `draftsvc` Codex login
- `/srv/neurips-draft/home/.claude` — private `draftsvc` Claude Code login
- `/srv/neurips-draft/jobs/<job>/case_packets` — uploaded case packets
- `/srv/neurips-draft/jobs/<job>/results` — checklists and sidecars

After the runtime is installed, authenticate once:

```bash
ssh -t root@DRAFT_VPS neurips-draft-login
ssh root@DRAFT_VPS neurips-draft-login --status
```

Claude Code 2.1.170 is installed by `install_runtime.sh` by default (override
with `CLAUDE_CODE_VERSION`), but it is used only by the
explicit secondary score lane. Authenticate that lane separately with a Claude
subscription login:

```bash
ssh -t root@DRAFT_VPS neurips-score-claude-login
ssh root@DRAFT_VPS neurips-score-claude-login --status
```

For a benchmark whose packet root contains `*/case_packet.md`, upload and submit:

```bash
JOB_ID=appworld_draft_001
ssh root@DRAFT_VPS neurips-draft-init "$JOB_ID"
rsync -az \
  /local/path/to/case_packets/ \
  root@DRAFT_VPS:/srv/neurips-draft/jobs/$JOB_ID/case_packets/
ssh root@DRAFT_VPS neurips-draft-submit "$JOB_ID"
```

The job continues under systemd after the SSH session closes. Inspect it with:

```bash
ssh root@DRAFT_VPS neurips-draft-status "$JOB_ID"
```

Fetch the complete results tree:

```bash
rsync -az \
  root@DRAFT_VPS:/srv/neurips-draft/jobs/$JOB_ID/results/ \
  /local/path/to/drafts/
```

Runtime defaults live in `/etc/neurips-draft.env`. `DRAFT_MODEL` and
`DRAFT_REASONING_EFFORT` default to `gpt-5.4` and `xhigh`.
`DRAFT_MAX_PARALLEL` controls regular packets and `DRAFT_LARGE_MAX_PARALLEL`
controls packets above the runner's 100 KB oversized threshold. The wrapper rejects
values above `DRAFT_MAX_ALLOWED_PARALLEL` (72 by default).

Additional `run_draft_batch.py` options can follow the job id, for example
`--quality-check agentdojo`, `--limit 10`, or `--force`. Provider, model, reasoning
effort, sandbox, and concurrency remain fixed by the server wrapper. Do not pass the
machine-specific `--appworld-v56-runtime-gate` on this generic Linux deployment.

## Score jobs on the same VPS

The score service keeps uploads, state, temporary homes, and outputs under
`/srv/neurips-score`. Codex remains the default and reuses the authenticated
`draftsvc` Codex login. It uses the canonical score prompt, a read-only ephemeral
Codex session, `gpt-5.4`, `reasoning-effort=xhigh`, and the default service tier
(fast mode is not enabled). Claude Code is an explicit secondary scorer; it uses
the separate `draftsvc` Claude subscription login, the `sonnet` alias, and
`effort=high`.

On Ubuntu 24.04, the installer also loads the narrowly scoped
`apparmor/neurips-codex` profile. This permits only the installed Codex native
binary to create the user namespace required by its Linux read-only sandbox; the
system-wide unprivileged-user-namespace restriction remains enabled.
Each score batch also runs a no-model-call sandbox self-test before preflight;
if read access or write blocking fails, the batch exits before spending quota.

Initialize a score job:

```bash
JOB_ID=tau3_score_001
ssh root@DRAFT_VPS neurips-score-init "$JOB_ID"
```

Upload one directory per score task. A task can represent any benchmark case/run
pair; use a distinct task id for different agents or repeated runs of one case:

```text
tasks/
  case57_agent_a/
    checklist.yaml
    evidence/
      raw_run.json
      native_run/
      logs/
      ...
```

For example:

```bash
rsync -az /local/checklist.yaml \
  root@DRAFT_VPS:/srv/neurips-score/jobs/$JOB_ID/tasks/case57_agent_a/checklist.yaml
rsync -az /local/run_artifacts/ \
  root@DRAFT_VPS:/srv/neurips-score/jobs/$JOB_ID/tasks/case57_agent_a/evidence/
ssh root@DRAFT_VPS neurips-score-submit "$JOB_ID"
ssh root@DRAFT_VPS neurips-score-status "$JOB_ID"
```

The command above still selects Codex. To request Claude Code for one new score
job, pass the scorer explicitly:

```bash
ssh root@DRAFT_VPS neurips-score-submit "$JOB_ID" --scorer claude-code
```

There is no automatic fallback between scorers. The Claude lane removes API-key,
Bedrock, Vertex, and Foundry auth variables, verifies a `claude.ai` subscription
login before preflight, disables user/project customizations, does not persist
sessions, and exposes only the read-only `Read`, `Glob`, and `Grep` tools.

The submit command validates every checklist and resolves every released evaluator
label before making any model call. It rejects symlinks, special files, hard links,
oversized jobs, input changes after preflight, missing labels, and non-schema drafts.
Uploaded inputs become root-owned and read-only for the score process.

Download outputs and the portable relative-path/hash manifest:

```bash
rsync -az \
  root@DRAFT_VPS:/srv/neurips-score/jobs/$JOB_ID/results/ \
  /local/path/to/scores/
```

`/etc/neurips-score.env` controls model, reasoning effort, timeout, retry, upload
limits, and concurrency. The installed shared-login default is one score at a time.
`SCORE_MAX_ALLOWED_PARALLEL=36` reserves a root-controlled ceiling, but increasing
parallelism should be done only after a separate shared-account rate-limit/stability
test. Draft and Score use the same Codex account and therefore share its quota.

The Claude lane has separate settings: `SCORE_CLAUDE_MODEL=sonnet`,
`SCORE_CLAUDE_REASONING_EFFORT=high`, `SCORE_CLAUDE_TIMEOUT_SECONDS=1800`,
and `SCORE_CLAUDE_MAX_PARALLEL=1`. Its root-controlled ceiling is
`SCORE_CLAUDE_MAX_ALLOWED_PARALLEL=72`, so the deployment can be configured for
up to 72 workers without changing code. This is a process ceiling, not an
Anthropic concurrency guarantee; raise the configured parallelism only after a
staged subscription rate-limit and disk/memory test.
