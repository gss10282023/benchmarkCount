"""Lock and audit the local BrowserGym/MiniWoB++ runtime."""

from __future__ import annotations

import argparse
import json
import re
from typing import Sequence

from evidence_system.contracts.miniwob_runtime_lock import (
    DEFAULT_CATALOGS,
    DEFAULT_SELECTED_SOURCES,
    MiniWoBRuntimeLockError,
    build_miniwob_runtime_lock,
    write_miniwob_runtime_lock,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--infra-config",
        required=True,
        help="Concrete local source/runtime infra used for probe and official-source hashing.",
    )
    parser.add_argument(
        "--execution-infra-config",
        help=(
            "Formal non-dry-run execution infra. Strongly recommended; when omitted, --infra-config "
            "is used as a backward-compatible fallback and formal execution compatibility remains unproven."
        ),
    )
    parser.add_argument("--agents-config", default="configs/agents.yaml")
    parser.add_argument("--catalog", action="append", default=[], help="Old catalog; pass exactly twice.")
    parser.add_argument(
        "--selected-sources",
        action="append",
        default=[],
        help="Old selected-source file; pass first50 then second50.",
    )
    parser.add_argument("--old-runs-root", default="results/full/miniwob")
    parser.add_argument("--old-scores-root", default="results/scores/full/miniwob")
    parser.add_argument("--score-prompt", default="neurips_ed_track_minimal/prompts/score_evidence_with_codex.prompt.md")
    parser.add_argument("--score-schema", default="neurips_ed_track_minimal/schemas/evidence_score.schema.json")
    parser.add_argument("--score-script", default="neurips_ed_track_minimal/scripts/score_evidence_with_codex.py")
    parser.add_argument("--base-seed", type=int, default=7)
    parser.add_argument(
        "--release-component-sha256",
        action="append",
        default=[],
        metavar="PATH=SHA256",
        help="Old-release code hash. Repeat for adapter, worker, runtime, and jobs.py.",
    )
    parser.add_argument("--release-chromium-sha256")
    parser.add_argument("--release-chromium-version")
    parser.add_argument("--release-html-inventory-sha256")
    parser.add_argument("--output", required=True)
    parser.add_argument("--require-direct-merge", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        component_hashes = _parse_component_hashes(args.release_component_sha256)
        payload = build_miniwob_runtime_lock(
            infra_config_path=args.infra_config,
            execution_infra_config_path=args.execution_infra_config,
            agents_config_path=args.agents_config,
            catalog_paths=args.catalog or DEFAULT_CATALOGS,
            selected_sources_paths=args.selected_sources or DEFAULT_SELECTED_SOURCES,
            old_runs_root=args.old_runs_root,
            old_scores_root=args.old_scores_root,
            score_prompt_path=args.score_prompt,
            score_schema_path=args.score_schema,
            score_script_path=args.score_script,
            expected_release_component_hashes=component_hashes,
            expected_release_chromium_sha256=args.release_chromium_sha256,
            expected_release_chromium_version=args.release_chromium_version,
            expected_release_html_inventory_sha256=args.release_html_inventory_sha256,
            base_seed=args.base_seed,
        )
        output = write_miniwob_runtime_lock(args.output, payload)
    except (MiniWoBRuntimeLockError, ValueError) as exc:
        error = {"status": "error", "error": str(exc)}
        print(json.dumps(error, indent=2, sort_keys=True) if args.json else f"ERROR: {exc}")
        return 2

    summary = {
        "status": payload["status"],
        "lock_gate_passed": payload["lock_gate_passed"],
        "direct_merge_eligible": payload["direct_merge_eligible"],
        "reasons": payload["reasons"],
        "runtime_lock_sha256": payload["runtime_lock_sha256"],
        "output": str(output),
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"status={summary['status']} lock_gate_passed={summary['lock_gate_passed']} "
            f"direct_merge_eligible={summary['direct_merge_eligible']} output={summary['output']}"
        )
        for reason in summary["reasons"]:
            print(f"- {reason}")
    if not payload["lock_gate_passed"]:
        return 1
    if args.require_direct_merge and not payload["direct_merge_eligible"]:
        return 1
    return 0


def _parse_component_hashes(values: Sequence[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        path, separator, digest = value.rpartition("=")
        if not separator or not path or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"invalid --release-component-sha256 value: {value!r}")
        if path in parsed:
            raise ValueError(f"duplicate release component path: {path}")
        parsed[path] = digest
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
