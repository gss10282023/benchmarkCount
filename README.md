# Evidence System Bootstrap

This repository contains the Step 2 package skeleton for the evidence-envelope benchmark experiment system.

The current state is intentionally limited:

- Formal code lives under `src/evidence_system/`.
- Existing paper, docs, configs, experiments, and preserved result-output dependencies remain in place.
- Adapter, scorer, deployment, orchestration, statistics, paper-output, release, and LLM logic are bootstrap placeholders only.
- Commands that would run or mutate formal experiments fail closed unless called in explicit bootstrap-check mode.

Canonical formal entry points use:

```bash
python -m evidence_system.cli.<command>
```

The legacy `scripts/*.py` entry points are not created in this step. If wrappers are added later, they must only delegate to package CLIs and must not contain unique formal logic.

## Bootstrap Checks

After installing test dependencies, run:

```bash
python -m pytest
python -m evidence_system.cli.validate_config
```

On systems where the interpreter is named `python3`, use `python3 -m ...`.

## Secrets

Do not put real API keys, SSH private keys, credentials, or private prompt logs in repository files. Use environment variable names and local paths only.
