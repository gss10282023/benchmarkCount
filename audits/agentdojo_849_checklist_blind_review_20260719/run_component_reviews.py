#!/usr/bin/env python3
"""Run outcome-blind Codex semantic reviews for 132 AgentDojo components."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import threading
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


AUDIT_ROOT = Path(__file__).resolve().parent
REVIEW_ROOT = AUDIT_ROOT / "component_reviews"
INDEX_PATH = REVIEW_ROOT / "index.json"
SCHEMA_PATH = AUDIT_ROOT / "component_review.schema.json"
PROMPT_PATH = AUDIT_ROOT / "component_review.prompt.md"
PRINT_LOCK = threading.Lock()
JSON_PATH_PART_RE = re.compile(
    r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\[(?P<index>\d+)\])?$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-parallel", type=int, default=20)
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument("--max-attempts", type=int, default=2)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_output_errors(payload: dict[str, Any]) -> list[str]:
    """Reject component-scope leakage that JSON Schema cannot express."""

    errors: list[str] = []
    component_type = str(payload.get("component_type") or "")
    native = payload.get("native") if isinstance(payload.get("native"), dict) else {}
    native_text = " ".join(
        str(native.get(field) or "")
        for field in ("criterion", "success_if", "fail_if", "undecided_if")
    ).lower()
    if component_type == "user" and re.search(
        r"\b(?:benign|both arms|paired aggregation|injection security|injected security|"
        r"security breach|breach predicate|three[- ]component|three paired)\b",
        native_text,
    ):
        errors.append("user native rule is not a reusable single-execution utility rule")
    if component_type == "injection" and re.search(
        r"\b(?:benign(?:-arm)?|user[- ]task utility|user utility)\b",
        native_text,
    ):
        errors.append("injection native rule leaks user-utility/benign scope")
    if re.search(
        r"native/(?:native_evaluator_(?:input|output)|run_summary)\.json|"
        r"released (?:per-record )?(?:label|result|boolean)|"
        r"this (?:review )?(?:workspace|input)|workspace contains|"
        r"input contains no retained|no run artifacts (?:are|were) (?:present|supplied)",
        native_text,
    ):
        errors.append("native rule contains prohibited result/workspace-specific text")
    native_pointers = [str(item) for item in native.get("source_pointers", [])]
    if not any(
        pointer.startswith("official/evaluator_oracle_excerpts.json::")
        for pointer in native_pointers
    ):
        errors.append("native rule lacks released evaluator/oracle support")
    native_artifacts = {str(item) for item in native.get("decisive_artifacts", [])}
    if not native_artifacts.intersection(
        {"native/trace_logs/**.json", "native/proxy_calls/*.json"}
    ):
        errors.append("native rule lacks independent trace/proxy evidence")

    stronger = payload.get("stronger") if isinstance(payload.get("stronger"), dict) else {}
    expected_goal = (
        "official/case_definition.json::user_goal.text"
        if component_type == "user"
        else "official/case_definition.json::injection_goal.text"
    )
    wrong_goal = (
        "official/case_definition.json::injection_goal.text"
        if component_type == "user"
        else "official/case_definition.json::user_goal.text"
    )
    gap_pattern = re.compile(
        r"(?is)(?:released|evaluator|native|oracle).{0,260}"
        r"(?:does not|doesn't|not |omit|only|without|fails|weaker|ignores|accepts|"
        r"never|loses|losing|discards)"
    )
    for condition in stronger.get("canonical_conditions", []) or []:
        if not isinstance(condition, dict):
            continue
        condition_id = str(condition.get("id") or "<missing>")
        pointers = [str(item) for item in condition.get("source_pointers", [])]
        if expected_goal not in pointers:
            errors.append(f"stronger {condition_id} lacks matching official goal pointer")
        if wrong_goal in pointers:
            errors.append(f"stronger {condition_id} cites the other component goal")
        if not any(
            pointer.startswith("official/evaluator_oracle_excerpts.json::")
            for pointer in pointers
        ):
            errors.append(f"stronger {condition_id} lacks evaluator gap support")
        if gap_pattern.search(str(condition.get("rationale") or "")) is None:
            errors.append(f"stronger {condition_id} does not explicitly state the native gap")
        artifacts = {str(item) for item in condition.get("decisive_artifacts", [])}
        if not artifacts.intersection(
            {"native/trace_logs/**.json", "native/proxy_calls/*.json"}
        ):
            errors.append(f"stronger {condition_id} lacks trace/proxy review evidence")
    return errors


def component_pointer_errors(payload: dict[str, Any], workspace: Path) -> list[str]:
    pointers = [
        str(item)
        for item in (payload.get("native") or {}).get("source_pointers", [])
    ]
    for condition in (payload.get("stronger") or {}).get("canonical_conditions", []) or []:
        if isinstance(condition, dict):
            pointers.extend(str(item) for item in condition.get("source_pointers", []))
    errors = []
    for pointer in pointers:
        source_path, separator, location = pointer.partition("::")
        source = workspace / "sources" / source_path
        if separator != "::" or not source.is_file():
            errors.append(f"unresolvable component source pointer: {pointer}")
            continue
        try:
            node: Any = load_json(source)
            for raw_part in location.split("."):
                match = JSON_PATH_PART_RE.fullmatch(raw_part)
                if match is None or not isinstance(node, dict):
                    raise ValueError(raw_part)
                name = match.group("name")
                if name not in node:
                    raise ValueError(raw_part)
                node = node[name]
                index = match.group("index")
                if index is not None:
                    if not isinstance(node, list) or int(index) >= len(node):
                        raise ValueError(raw_part)
                    node = node[int(index)]
        except (OSError, ValueError, json.JSONDecodeError):
            errors.append(f"unresolvable component source pointer: {pointer}")
    return errors


def valid_output(path: Path, validator: Draft202012Validator, item: dict[str, Any]) -> bool:
    if not path.is_file():
        return False
    try:
        payload = load_json(path)
    except Exception:
        return False
    if list(validator.iter_errors(payload)):
        return False
    if semantic_output_errors(payload):
        return False
    if component_pointer_errors(payload, Path(item["workspace"]).resolve()):
        return False
    return (
        payload.get("component_type") == item["component_type"]
        and payload.get("component_id") == item["component_id"]
    )


def review_one(
    item: dict[str, Any],
    *,
    model: str,
    reasoning_effort: str,
    timeout_seconds: int,
    max_attempts: int,
    validator: Draft202012Validator,
    prompt: str,
) -> dict[str, Any]:
    workspace = Path(item["workspace"]).resolve()
    output = Path(item["output"]).resolve()
    log = Path(item["log"]).resolve()
    stderr_log = log.with_suffix(".stderr.log")
    output.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)

    if valid_output(output, validator, item):
        return {"status": "reused", **item}

    command = [
        "codex",
        "exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'model_verbosity="low"',
        "-c",
        'service_tier="default"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(SCHEMA_PATH.resolve()),
        "-o",
        str(output),
        prompt,
    ]

    last_error = ""
    for attempt in range(1, max_attempts + 1):
        if output.exists():
            output.unlink()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            last_error = f"timeout after {timeout_seconds}s: {exc}"
            continue
        log.write_text(result.stdout or "", encoding="utf-8")
        stderr_log.write_text(result.stderr or "", encoding="utf-8")
        if result.returncode != 0:
            last_error = f"codex exit {result.returncode}: {(result.stderr or result.stdout)[-2000:]}"
            continue
        if valid_output(output, validator, item):
            return {"status": "completed", "attempt": attempt, **item}
        last_error = "output missing, schema-invalid, or component identity mismatch"

    return {"status": "failed", "error": last_error, **item}


def main() -> int:
    args = parse_args()
    if args.max_parallel < 1 or args.max_attempts < 1:
        raise SystemExit("parallelism and attempts must be positive")
    index = load_json(INDEX_PATH)
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = {
            executor.submit(
                review_one,
                item,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                timeout_seconds=args.timeout_seconds,
                max_attempts=args.max_attempts,
                validator=validator,
                prompt=prompt,
            ): item
            for item in index
        }
        for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            with PRINT_LOCK:
                print(
                    f"[{completed}/{len(index)}] {result['status']} "
                    f"{result['component_type']} {result['component_id']}",
                    flush=True,
                )

    results.sort(key=lambda item: (item["component_type"], item["component_id"]))
    (REVIEW_ROOT / "run_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))
    return 0 if not counts.get("failed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
