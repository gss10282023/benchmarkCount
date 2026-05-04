"""Schema registry skeleton.

Step 2 creates schema files as first-class paths. Step 3 replaces placeholders
with formal validation rules and validators.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from evidence_system.core.paths import resolve_repo_path


REQUIRED_SCHEMA_FILES = (
    "experiment_manifest.schema.json",
    "paper_mapping.schema.json",
    "job.schema.json",
    "agent_config.schema.json",
    "infra_config.schema.json",
    "raw_run.schema.json",
    "scored_record.schema.json",
    "infra_exclusion_record.schema.json",
    "failure_record.schema.json",
    "artifact_manifest.schema.json",
    "evidence_contract.schema.json",
    "contract_review.schema.json",
    "llm_call.schema.json",
    "human_review.schema.json",
    "human_time.schema.json",
    "audit_item.schema.json",
    "audit_label.schema.json",
    "rerun_record.schema.json",
    "stats_plan.schema.json",
    "bootstrap_plan.schema.json",
    "audit_sampling_plan.schema.json",
    "rerun_subset.schema.json",
    "aggregate_metrics.schema.json",
    "prediction_outcome.schema.json",
    "pairwise_matrix.schema.json",
    "denominator_audit.schema.json",
    "paper_output.schema.json",
    "freeze_manifest.schema.json",
    "deployment_manifest.schema.json",
    "release_artifact.schema.json",
)


@dataclass(frozen=True)
class SchemaRegistryStatus:
    schema_dir: str
    missing: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing


def schema_dir() -> Path:
    return resolve_repo_path("schemas")


def check_schema_files() -> SchemaRegistryStatus:
    base = schema_dir()
    missing = [name for name in REQUIRED_SCHEMA_FILES if not (base / name).exists()]
    return SchemaRegistryStatus(schema_dir=str(base), missing=missing)
