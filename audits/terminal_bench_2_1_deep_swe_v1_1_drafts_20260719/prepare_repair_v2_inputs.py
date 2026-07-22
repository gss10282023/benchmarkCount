#!/usr/bin/env python3
"""Stage outcome-blind inputs for the v2 repair of rejected checklist drafts.

The script copies only packet material, original frozen drafts, and the existing
outcome-blind review findings.  It intentionally never reads or copies run data,
agent trajectories, per-record rewards/labels, evidence scores, or conflicts.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


AUDIT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AUDIT_ROOT.parents[1]
SOURCE_DRAFT_ROOT = AUDIT_ROOT / "drafts"
REPAIR_ROOT = AUDIT_ROOT / "repair_v2"
INPUT_ROOT = REPAIR_ROOT / "inputs"
CONTEXT_OUTPUT_ROOT = INPUT_ROOT / "repair_context"
ORIGINAL_OUTPUT_ROOT = INPUT_ROOT / "original_drafts"
REVIEW_OUTPUT_ROOT = INPUT_ROOT / "prior_reviews"
REPAIR_PROMPT = AUDIT_ROOT / "repair_v2_prompt.md"
PACKET_ROOTS = {
    "terminal_bench_2_1": REPO_ROOT / "experiments/case_packets/terminal_bench_2_1",
    "deep_swe_v1_1": REPO_ROOT / "experiments/case_packets/deep_swe_v1_1",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def jsonl(path: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected object in {path}")
        output.append(value)
    return output


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def copy_file_once(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(source) != sha256_file(destination):
            raise RuntimeError(f"existing staged file differs: {destination}")
        return
    shutil.copy2(source, destination)


def context_markdown(
    *,
    case_id: str,
    benchmark: str,
    original: str,
    review: Mapping[str, Any],
    revision_validation: Mapping[str, Any] | None,
) -> str:
    findings = review.get("blocking_findings")
    findings = findings if isinstance(findings, list) else []
    clean_findings = [item for item in findings if isinstance(item, Mapping)]
    errors = revision_validation.get("errors") if isinstance(revision_validation, Mapping) else []
    errors = errors if isinstance(errors, list) else []
    lines = [
        REPAIR_PROMPT.read_text(encoding="utf-8").rstrip(),
        "",
        "# Case-specific outcome-blind repair context",
        "",
        f"- benchmark: `{benchmark}`",
        f"- case_unit_id: `{case_id}`",
        "- This context is diagnostic only. The case packet is the authoritative source.",
        "- Do not use any proposed prior revision as authority; it may contain invalid pointers.",
        "",
        "## Original frozen checklist",
        "",
        "```yaml",
        original.rstrip(),
        "```",
        "",
        "## Prior independent review findings to repair",
        "",
    ]
    for finding in clean_findings:
        evidence = finding.get("evidence")
        evidence = evidence if isinstance(evidence, list) else []
        lines.extend(
            [
                f"### {finding.get('checklist_item_id')}: {finding.get('id')}",
                str(finding.get("message") or ""),
                "",
                "Required correction: " + str(finding.get("required_change") or ""),
                "",
                "Cited diagnostic locations: " + ", ".join(str(item) for item in evidence),
                "",
            ]
        )
    if errors:
        lines.extend(
            [
                "## Validation errors in the prior suggested replacement",
                "",
                "The prior reviewer-produced replacement was not applied. Avoid repeating these errors:",
                "",
            ]
        )
        lines.extend(f"- `{error}`" for error in errors)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    semantic_records = jsonl(AUDIT_ROOT / "semantic_review_records.jsonl")
    review_root = AUDIT_ROOT / "semantic_reviews"
    selected = [record for record in semantic_records if record.get("decision") == "revise"]
    if len(selected) != 132:
        raise RuntimeError(f"expected 132 revision-required cases, found {len(selected)}")
    selected.sort(key=lambda item: str(item["case_unit_id"]))
    records: list[dict[str, Any]] = []
    for record in selected:
        case_id = str(record["case_unit_id"])
        benchmark = str(record["benchmark"])
        packet_source = PACKET_ROOTS[benchmark] / case_id
        original_source = SOURCE_DRAFT_ROOT / case_id / "checklist.yaml"
        review_source = review_root / case_id / "review.json"
        if not packet_source.is_dir() or not original_source.is_file() or not review_source.is_file():
            raise RuntimeError(f"missing repair input for {case_id}")
        original_destination = ORIGINAL_OUTPUT_ROOT / case_id / "checklist.yaml"
        review_destination = REVIEW_OUTPUT_ROOT / case_id / "review.json"
        copy_file_once(original_source, original_destination)
        copy_file_once(review_source, review_destination)
        review = load_json(review_source)
        context_destination = CONTEXT_OUTPUT_ROOT / case_id / "repair_context.md"
        context = context_markdown(
            case_id=case_id,
            benchmark=benchmark,
            original=original_source.read_text(encoding="utf-8"),
            review=review,
            revision_validation=(
                record.get("revision_validation")
                if isinstance(record.get("revision_validation"), Mapping)
                else None
            ),
        )
        if context_destination.exists():
            if context_destination.read_text(encoding="utf-8") != context:
                raise RuntimeError(f"existing repair context differs: {context_destination}")
        else:
            context_destination.parent.mkdir(parents=True, exist_ok=True)
            context_destination.write_text(context, encoding="utf-8")
        records.append(
            {
                "benchmark": benchmark,
                "case_unit_id": case_id,
                "packet_path": str((packet_source / "case_packet.md").relative_to(REPO_ROOT)),
                "packet_sha256": sha256_file(packet_source / "case_packet.md"),
                "original_checklist_path": str(original_destination.relative_to(REPO_ROOT)),
                "original_checklist_sha256": sha256_file(original_destination),
                "review_path": str(review_destination.relative_to(REPO_ROOT)),
                "review_sha256": sha256_file(review_destination),
                "repair_context_path": str(context_destination.relative_to(REPO_ROOT)),
                "repair_context_sha256": sha256_file(context_destination),
                "failed_review_item_ids": record.get("failed_item_ids", []),
            }
        )
    manifest = {
        "schema_version": "tb21_deepswe11_outcome_blind_repair_v2_inputs/v1",
        "created_at": utc_now(),
        "case_count": len(records),
        "repair_prompt": str(REPAIR_PROMPT.relative_to(REPO_ROOT)),
        "repair_prompt_sha256": sha256_file(REPAIR_PROMPT),
        "source_boundary": [
            "case packet and raw official source tree",
            "original frozen checklist",
            "prior outcome-blind review findings",
            "prior suggested-revision validation errors",
        ],
        "excluded_inputs": [
            "agent outcomes",
            "agent trajectory contents",
            "concrete retained execution-artifact contents",
            "per-record evaluator reward/result/label values",
            "evidence-scoring outputs",
            "benchmark-conflict records",
        ],
        "records": records,
    }
    write_json(REPAIR_ROOT / "repair_input_manifest.json", manifest)
    print(json.dumps({
        "case_count": len(records),
        "input_root": str(INPUT_ROOT.relative_to(REPO_ROOT)),
        "manifest": str((REPAIR_ROOT / "repair_input_manifest.json").relative_to(REPO_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
