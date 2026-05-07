# VPS Runtime Specification

## Machine Roles

Formal scheduling uses machine roles:

```text
webarena_vps
osworld_vps
other_vps
local_androidworld
```

Domain routing:

- `webarena_verified` runs only on `webarena_vps`.
- `osworld_verified` runs only on `osworld_vps`.
- `androidworld` runs only on `local_androidworld`.
- `agentdojo`, `appworld`, `tau3_retail`, `workarena`, `judge_only`, `maintenance_update`, and `matched_budget_controls` run on `other_vps` unless the locked infra manifest says otherwise.

`configs/infra.yaml` is the source for hostnames, users, ports, key paths, remote workdirs, Python/conda/venv/docker settings, benchmark install directories, runner directories, concurrency, resources, log directories, result directories, disk thresholds, network targets, asset paths, and scheduler type. Formal code must not hardcode those values.

## Secret Handling

SSH private key contents, API keys, live credentials, and service secrets must never be written to docs, logs, manifests, review packets, or release metadata. Config may reference an environment variable name or local key path when needed for runtime validation, but release and review packets must not expose secret values.

## Deployment CLIs

Deployment and runtime commands are package CLIs:

```text
python -m evidence_system.cli.check_infra
python -m evidence_system.cli.deploy_all
python -m evidence_system.cli.deploy_webarena
python -m evidence_system.cli.deploy_osworld
python -m evidence_system.cli.deploy_other_vps
python -m evidence_system.cli.deploy_local_androidworld
python -m evidence_system.cli.monitor
python -m evidence_system.cli.collect_results
python -m evidence_system.cli.resume_failed
python -m evidence_system.cli.webarena_runtime reset
python -m evidence_system.cli.webarena_runtime baseline-check
```

Any `scripts/*.py` equivalent is a thin wrapper.

## Infra Check

`check_infra` validates without running formal experiments:

- SSH reachability where enabled.
- rsync availability.
- Python/conda/venv/docker readiness.
- benchmark install and assets.
- result directories writable.
- dry-run path not pointing at formal full results.
- LLM API key environment variables exist where needed, without logging values.
- disk space.
- network targets.
- machine role uniqueness and domain routing.
- current git commit and config hash.
- deployment manifest consistency.

Failure blocks deploy/preflight/full run as appropriate.

## Deployment Manifest

Deployment writes `deployment_manifest/v1`:

```json
{
  "schema_version": "deployment_manifest/v1",
  "deployment_id": "...",
  "created_at": "...",
  "git_commit_hash": "...",
  "infra_config_hash": "...",
  "machines": [],
  "benchmarks": [],
  "domain_machine_constraints": {},
  "status": "ready|blocked"
}
```

Deployment must be idempotent and must not overwrite formal raw logs, full results, scored records, freeze files, or paper outputs.

## Monitoring

`monitor` reports machine status, domain progress, task status, failure category, retry status, cost/log availability, and stuck jobs. It must not treat UNRESOLVE as execution failure and must not treat agent-caused FAIL as infra exclusion. It can show LLM costs for operational monitoring, but those values do not fill `tab:cost`.

## Collection And Resume

`collect_results` preserves original machine path, run id, attempt id, config hash, git commit, raw logs, artifact manifests, LLM logs, and failure records. It must be repeatable without duplicate samples.

`resume_failed` retries only recoverable infra/pre-run/logging failures under policy. It preserves all attempts and identifies exactly one final_attempt. It does not retry UNRESOLVE as a failure.

`webarena_runtime reset` performs per-site WebArena environment reinitialization on the configured `webarena_vps` using the benchmark reset command declared in `configs/infra.yaml`. For the current original `web-arena-x/webarena` path, that command maps to the repo-local reset script that recreates the official site containers and reapplies base URL configuration. `webarena_runtime baseline-check` verifies container liveness, site reachability, and fixed non-LLM sentinels (including the shopping-admin review query and a map routing distance probe) so formal runs can distinguish environment drift from agent failure. `run_full` automatically runs a `with_reset=True` WebArena baseline-check once before the first `webarena_verified` batch executes in a non-plan-only full run and blocks the batch if the runtime check fails.
