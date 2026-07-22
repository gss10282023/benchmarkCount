#!/usr/bin/env python3
"""Generate 116 independent semantic-review proposals with six Codex workers.

The entrypoint is intended to be executed from the toolchain snapshot created by
``prepare_semantic_review_prelock.py``.  Each Codex call is ephemeral,
read-only, login-authenticated, and receives only the exact prelocked packet,
raw checklist, review prompt, and output schema.  A successful result remains a
model proposal with ``promotion_authorized=false``.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import json
import os
import re
import signal
import shutil
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import semantic_review_common as review_common
from semantic_review_common import (
    CONCURRENCY_AUDIT_SCHEMA_VERSION,
    CONCURRENCY_EVENT_SCHEMA_VERSION,
    CONFIG_SCHEMA_VERSION,
    EXACT_CODEX_LOGIN_STATUS,
    EXPECTED_CASE_COUNT,
    EXPECTED_MODEL,
    EXPECTED_PARALLELISM,
    EXPECTED_REASONING_EFFORT,
    PRELOCK_SCHEMA_VERSION,
    RECEIPT_SCHEMA_VERSION,
    REPO_ROOT,
    WORK_ROOT,
    SemanticReviewError,
    add_self_hash,
    build_proposal,
    canonical_runtime_tree,
    codex_usage,
    event_response_id,
    file_binding,
    load_json,
    load_jsonl_events,
    load_yaml_mapping,
    model_body_schema,
    object_sha256,
    parse_case_packet,
    reasoning_fragments,
    repo_relative,
    require_iso8601,
    resolve_repo_path,
    schema_errors,
    sha256_bytes,
    sha256_file,
    utc_now,
    validate_proposal,
    validate_review_body,
    verify_file_binding,
    verify_issue_history,
    verify_python_runtime_trees,
    verify_semantic_concurrency_evidence,
    verify_self_hash,
    write_json_atomic,
    write_text_atomic,
)


SCRIPT = Path(__file__).resolve()
PRINT_LOCK = threading.Lock()


@dataclass(frozen=True)
class ReviewContext:
    prelock_path: Path
    prelock: dict[str, Any]
    config_path: Path
    config: dict[str, Any]
    output_root: Path
    prompt_path: Path
    proposal_schema_path: Path
    body_schema_path: Path
    checklist_schema_path: Path
    proposal_schema: dict[str, Any]
    body_schema: dict[str, Any]
    checklist_schema: dict[str, Any]
    codex_binary: Path
    python_runtime: dict[str, Any]


class ProcessConcurrencyAudit:
    """Append-only, self-hashed Codex subprocess lifecycle evidence."""

    def __init__(
        self,
        root: Path,
        *,
        prelock_sha256: str,
        case_order: list[str],
        resume: bool,
        process_observer: Mapping[str, Any],
    ) -> None:
        self.root = root
        self.events_path = root / "events.jsonl"
        self.audit_path = root / "audit.json"
        if resume:
            if not root.is_dir() or not self.events_path.is_file() or self.audit_path.exists():
                raise SemanticReviewError(
                    "resume requires unfinished concurrency events and no finalized audit"
                )
        else:
            root.mkdir(parents=True, exist_ok=False)
            self.events_path.open("xb").close()
        self.prelock_sha256 = prelock_sha256
        self.case_order = list(case_order)
        self.process_observer = dict(process_observer)
        observer_path = Path(str(self.process_observer.get("invocation_path") or ""))
        observer_resolved = Path(str(self.process_observer.get("resolved_path") or ""))
        if (
            not observer_path.is_file()
            or observer_path.resolve(strict=True) != observer_resolved
            or sha256_file(observer_resolved) != self.process_observer.get("sha256")
        ):
            raise SemanticReviewError("frozen process observer differs")
        self.lock = threading.Lock()
        self.active: dict[tuple[str, int], int] = {}
        self.started_cases: set[str] = set()
        self.sequence = 0
        self.previous_hash: str | None = None
        self.peak = 0
        self.start_count = 0
        self.stop_count = 0
        if resume:
            self._load_existing()

    def _load_existing(self) -> None:
        previous_hash: str | None = None
        reconstructed: dict[tuple[str, int], int] = {}
        for sequence, raw in enumerate(self.events_path.read_text(encoding="utf-8").splitlines()):
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise SemanticReviewError(
                    f"cannot resume malformed concurrency event {sequence}: {exc}"
                ) from exc
            if not isinstance(event, Mapping):
                raise SemanticReviewError(f"cannot resume non-object concurrency event {sequence}")
            verify_self_hash(event, "event_sha256", f"resume concurrency event {sequence}")
            if (
                event.get("schema_version") != CONCURRENCY_EVENT_SCHEMA_VERSION
                or event.get("sequence") != sequence
                or event.get("previous_event_sha256") != previous_hash
                or event.get("prelock_sha256") != self.prelock_sha256
            ):
                raise SemanticReviewError(f"resume concurrency chain differs at {sequence}")
            key = (str(event.get("case_unit_id") or ""), int(event.get("attempt_index") or 0))
            pid = int(event.get("pid") or 0)
            if key[0] not in set(self.case_order) or key[1] <= 0 or pid <= 0:
                raise SemanticReviewError(f"resume concurrency identity differs at {sequence}")
            if event.get("event") == "start":
                if key in reconstructed:
                    raise SemanticReviewError(f"resume has duplicate process start: {key}")
                reconstructed[key] = pid
                self.started_cases.add(key[0])
                self.start_count += 1
            elif event.get("event") == "stop":
                if reconstructed.get(key) != pid:
                    raise SemanticReviewError(f"resume has unmatched process stop: {key}")
                del reconstructed[key]
                self.stop_count += 1
            else:
                raise SemanticReviewError(f"resume has invalid event kind at {sequence}")
            observed_active = [
                {"case_unit_id": item[0], "attempt_index": item[1], "pid": reconstructed[item]}
                for item in sorted(reconstructed)
            ]
            if event.get("active") != observed_active or event.get("active_count") != len(
                observed_active
            ):
                raise SemanticReviewError(f"resume active state differs at {sequence}")
            self.peak = max(self.peak, len(observed_active))
            previous_hash = str(event["event_sha256"])
            self.sequence = sequence + 1
        if reconstructed:
            raise SemanticReviewError(
                "cannot resume after an unclosed Codex process; archive the incident first"
            )
        self.previous_hash = previous_hash

    def _record(self, kind: str, case_id: str, attempt_index: int, pid: int) -> None:
        key = (case_id, attempt_index)
        with self.lock:
            process_observation: list[dict[str, Any]] = []
            if kind == "start":
                if key in self.active:
                    raise SemanticReviewError(f"duplicate tracked Codex start: {key}")
                if len(self.active) + 1 == EXPECTED_PARALLELISM:
                    process_observation = self._observe_live_processes(
                        [*self.active.values(), pid]
                    )
                self.active[key] = pid
                self.started_cases.add(case_id)
                self.start_count += 1
            elif kind == "stop":
                if self.active.get(key) != pid:
                    raise SemanticReviewError(f"unmatched tracked Codex stop: {key}")
                del self.active[key]
                self.stop_count += 1
            else:
                raise SemanticReviewError(f"invalid tracked process event: {kind}")
            active = [
                {
                    "case_unit_id": item[0],
                    "attempt_index": item[1],
                    "pid": self.active[item],
                }
                for item in sorted(self.active)
            ]
            if len(active) > EXPECTED_PARALLELISM:
                raise SemanticReviewError("semantic-review process count exceeded six")
            self.peak = max(self.peak, len(active))
            event = {
                "schema_version": CONCURRENCY_EVENT_SCHEMA_VERSION,
                "sequence": self.sequence,
                "event": kind,
                "case_unit_id": case_id,
                "attempt_index": attempt_index,
                "pid": pid,
                "monotonic_ns": time.monotonic_ns(),
                "recorded_at": utc_now(),
                "active_count": len(active),
                "active": active,
                "process_observation": process_observation,
                "previous_event_sha256": self.previous_hash,
                "prelock_sha256": self.prelock_sha256,
            }
            event = add_self_hash(event, "event_sha256")
            with self.events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.previous_hash = event["event_sha256"]
            self.sequence += 1

    def _observe_live_processes(self, pids: list[int]) -> list[dict[str, Any]]:
        expected = sorted(set(pids))
        completed = subprocess.run(
            [
                str(self.process_observer["invocation_path"]),
                "-o",
                "pid=,pgid=,command=",
                "-p",
                ",".join(str(pid) for pid in expected),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        rows: list[dict[str, Any]] = []
        for raw in (completed.stdout or "").splitlines():
            match = re.match(r"^\s*([0-9]+)\s+([0-9]+)\s+(.+?)\s*$", raw)
            if match is None:
                continue
            pid = int(match.group(1))
            pgid = int(match.group(2))
            command = match.group(3)
            try:
                tokens = shlex.split(command)
            except ValueError:
                tokens = []
            command_is_codex_exec = (
                "exec" in tokens
                and any("codex" in Path(token).name.casefold() for token in tokens)
            )
            rows.append(
                {
                    "pid": pid,
                    "pgid": pgid,
                    "command_sha256": sha256_bytes(command.encode("utf-8")),
                    "command_is_codex_exec": command_is_codex_exec,
                }
            )
        rows.sort(key=lambda row: row["pid"])
        if (
            completed.returncode != 0
            or [row["pid"] for row in rows] != expected
            or any(row["pgid"] != row["pid"] for row in rows)
            or any(row["command_is_codex_exec"] is not True for row in rows)
        ):
            raise SemanticReviewError(
                f"/bin/ps did not prove all active Codex exec process groups: expected={expected}, "
                f"observed={[row['pid'] for row in rows]}, "
                f"pgid_matches={[row['pgid'] == row['pid'] for row in rows]}, "
                f"codex_exec={[row['command_is_codex_exec'] for row in rows]}"
            )
        return rows

    def start(self, case_id: str, attempt_index: int, pid: int) -> None:
        self._record("start", case_id, attempt_index, pid)

    def stop(self, case_id: str, attempt_index: int, pid: int) -> None:
        self._record("stop", case_id, attempt_index, pid)

    def finalize(self) -> dict[str, Any]:
        with self.lock:
            if self.active:
                raise SemanticReviewError("cannot finalize concurrency audit with active processes")
            covered = [case_id for case_id in self.case_order if case_id in self.started_cases]
            passed = (
                covered == self.case_order
                and self.peak == EXPECTED_PARALLELISM
                and self.start_count == self.stop_count
            )
            audit = {
                "schema_version": CONCURRENCY_AUDIT_SCHEMA_VERSION,
                "status": "pass" if passed else "fail",
                "configured_workers": EXPECTED_PARALLELISM,
                "observed_peak_active_processes": self.peak,
                "event_count": self.sequence,
                "process_start_count": self.start_count,
                "process_stop_count": self.stop_count,
                "covered_case_count": len(covered),
                "covered_cases": covered,
                "final_event_sha256": self.previous_hash,
                "prelock_sha256": self.prelock_sha256,
                "events": file_binding(self.events_path),
                "process_observer": copy.deepcopy(self.process_observer),
                "completed_at": utc_now(),
            }
            audit = add_self_hash(audit, "audit_sha256")
            write_json_atomic(self.audit_path, audit)
        if not passed:
            raise SemanticReviewError("semantic-review run did not prove exact-six concurrency")
        return verify_semantic_concurrency_evidence(
            events_path=self.events_path,
            audit_path=self.audit_path,
            expected_case_order=self.case_order,
            expected_prelock_sha256=self.prelock_sha256,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path, help="Exact semantic-review prelock.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Retain only already completed, fully revalidated case results and fill the rest.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Exercise schemas and full/compact packet parsers without a model call or writes.",
    )
    parser.add_argument(
        "--concurrency-self-test",
        action="store_true",
        help="Run a no-model 116-case exact-six process-evidence/tamper test.",
    )
    return parser.parse_args()


def _verify_binding_tree(value: Any, label: str) -> None:
    if isinstance(value, Mapping) and {"path", "sha256", "size_bytes"}.issubset(value):
        verify_file_binding(value, label, inside_candidate=True)
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _verify_binding_tree(nested, f"{label}.{key}")
        return
    raise SemanticReviewError(f"{label} is neither a file binding nor a binding map")


def _role(prelock: Mapping[str, Any], name: str) -> Path:
    tools = prelock.get("tool_bindings")
    if not isinstance(tools, Mapping) or name not in tools:
        raise SemanticReviewError(f"review prelock is missing tool role {name}")
    return verify_file_binding(tools[name], f"tool role {name}", inside_candidate=True)


def load_context(prelock_path: Path) -> ReviewContext:
    prelock_path = prelock_path.resolve()
    prelock = load_json(prelock_path, "semantic-review prelock")
    if prelock.get("schema_version") != PRELOCK_SCHEMA_VERSION:
        raise SemanticReviewError("semantic-review prelock schema is not v1")
    if prelock.get("status") != "frozen_before_first_review_model_call":
        raise SemanticReviewError("semantic-review prelock status is not frozen-before-call")
    verify_self_hash(prelock, "prelock_sha256", "semantic-review prelock")
    if prelock.get("case_count") != EXPECTED_CASE_COUNT:
        raise SemanticReviewError("semantic-review prelock does not bind 116 cases")
    case_order = list(prelock.get("case_order") or [])
    case_inputs = list(prelock.get("case_inputs") or [])
    if (
        len(case_order) != EXPECTED_CASE_COUNT
        or len(set(case_order)) != EXPECTED_CASE_COUNT
        or len(case_inputs) != EXPECTED_CASE_COUNT
        or prelock.get("case_order_sha256") != object_sha256(case_order)
        or prelock.get("case_inputs_sha256") != object_sha256(case_inputs)
    ):
        raise SemanticReviewError("semantic-review case universe/order hash is invalid")
    for rank, row in enumerate(case_inputs):
        if not isinstance(row, Mapping):
            raise SemanticReviewError("semantic-review case input is not an object")
        core = dict(row)
        claimed = core.pop("case_input_sha256", None)
        if claimed != object_sha256(core):
            raise SemanticReviewError(f"case input self hash fails at rank {rank}")
        if (
            row.get("selection_rank") != rank
            or row.get("case_unit_id") != case_order[rank]
            or row.get("task_id") != case_order[rank]
            or row.get("packet_kind") != "full"
        ):
            raise SemanticReviewError(f"case input order mismatch at rank {rank}")
        _verify_binding_tree(row.get("input_bindings"), f"{case_order[rank]} inputs")
        issue_path = verify_file_binding(
            (row.get("input_bindings") or {}).get("issue_history"),
            f"{case_order[rank]} issue history",
            inside_candidate=True,
        )
        issue_history = load_json(issue_path, f"{case_order[rank]} issue history")
        verify_issue_history(issue_history, case_id=case_order[rank], rank=rank)
        if (
            row.get("issue_history_sha256") != issue_history.get("issue_history_sha256")
            or row.get("audit_case_sha256") != issue_history.get("audit_case_sha256")
        ):
            raise SemanticReviewError(f"{case_order[rank]} issue-history id differs")

    config_binding = prelock.get("review_config")
    if not isinstance(config_binding, Mapping):
        raise SemanticReviewError("semantic-review prelock has no review_config binding")
    config_path = verify_file_binding(config_binding, "review config", inside_candidate=True)
    config = load_json(config_path, "review config")
    if config.get("schema_version") != CONFIG_SCHEMA_VERSION or config.get("status") != "prelocked":
        raise SemanticReviewError("semantic-review config schema/status is invalid")
    verify_self_hash(config, "config_sha256", "semantic-review config")
    if config_binding.get("config_sha256") != config.get("config_sha256"):
        raise SemanticReviewError("review config internal hash differs from prelock")
    expected_config = {
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "sandbox": "read-only",
        "ephemeral": True,
        "ignore_user_config": True,
        "max_parallel": EXPECTED_PARALLELISM,
        "case_count": EXPECTED_CASE_COUNT,
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
    }
    for key, expected in expected_config.items():
        if config.get(key) != expected:
            raise SemanticReviewError(f"review config {key} is not {expected!r}")
    if int(config.get("max_attempts", 0)) <= 0 or int(config.get("codex_timeout_seconds", 0)) <= 0:
        raise SemanticReviewError("review retry/timeout configuration is invalid")

    runner_path = _role(prelock, "batch_runner")
    if runner_path.resolve() != SCRIPT:
        raise SemanticReviewError(
            "run the byte-prelocked snapshot batch_runner, not a mutable source copy"
        )
    prompt_path = _role(prelock, "review_prompt")
    proposal_schema_path = _role(prelock, "proposal_schema")
    body_schema_path = _role(prelock, "model_output_schema")
    checklist_schema_path = _role(prelock, "checklist_schema")
    _role(prelock, "bootstrap")
    runtime_path = _role(prelock, "python_runtime")
    common_path = _role(prelock, "common")
    if Path(review_common.__file__).resolve() != common_path.resolve():
        raise SemanticReviewError("batch runner imported a non-prelocked common module")
    _role(prelock, "independent_validator")
    snapshot_path = verify_file_binding(
        prelock.get("toolchain_snapshot"), "toolchain snapshot manifest", inside_candidate=True
    )
    snapshot = load_json(snapshot_path, "toolchain snapshot manifest")
    verify_self_hash(snapshot, "snapshot_sha256", "toolchain snapshot manifest")
    if prelock["toolchain_snapshot"].get("snapshot_sha256") != snapshot.get("snapshot_sha256"):
        raise SemanticReviewError("snapshot internal hash differs from prelock")
    if snapshot.get("roles") != prelock.get("tool_bindings"):
        raise SemanticReviewError("snapshot role index differs from review prelock")
    if (
        prelock.get("isolated_bootstrap") != config.get("isolated_bootstrap")
        or (prelock.get("isolated_bootstrap") or {}).get("entrypoint")
        != (prelock.get("tool_bindings") or {}).get("bootstrap")
        or config.get("toolchain_exact_tree_sha256")
        != (prelock.get("toolchain_exact_tree") or {}).get("tree_sha256")
    ):
        raise SemanticReviewError("isolated bootstrap/toolchain binding differs")
    runtime_binding = prelock.get("python_runtime")
    if (
        not isinstance(runtime_binding, Mapping)
        or verify_file_binding(runtime_binding, "Python runtime", inside_candidate=True)
        != runtime_path
        or config.get("python_runtime") != runtime_binding
    ):
        raise SemanticReviewError("Python runtime binding differs across prelock/config/tools")
    python_runtime = load_json(runtime_path, "Python runtime")
    verify_self_hash(python_runtime, "runtime_sha256", "Python runtime")
    if python_runtime.get("runtime_sha256") != runtime_binding.get("runtime_sha256"):
        raise SemanticReviewError("Python runtime internal hash differs")
    security_payload = prelock.get("security_content_payload")
    execution_payload = prelock.get("execution_security_payload")
    if (
        not isinstance(security_payload, Mapping)
        or object_sha256(security_payload) != prelock.get("security_content_address")
        or not isinstance(execution_payload, Mapping)
        or object_sha256(execution_payload) != prelock.get("execution_security_address")
    ):
        raise SemanticReviewError("semantic-review security content address differs")
    expected_execution_payload = {
        "security_content_address": prelock["security_content_address"],
        "case_inputs_sha256": prelock["case_inputs_sha256"],
        "config_sha256": config["config_sha256"],
        "python_runtime_sha256": python_runtime["runtime_sha256"],
        "toolchain_snapshot_sha256": snapshot["snapshot_sha256"],
        "toolchain_exact_tree_sha256": (prelock.get("toolchain_exact_tree") or {}).get(
            "tree_sha256"
        ),
        "bootstrap_launcher_sha256": (prelock.get("isolated_bootstrap") or {}).get(
            "launcher_sha256"
        ),
        "bootstrap_entrypoint_sha256": (prelock.get("isolated_bootstrap") or {}).get(
            "entrypoint_sha256"
        ),
    }
    if dict(execution_payload) != expected_execution_payload:
        raise SemanticReviewError("semantic-review execution security payload differs")
    if getattr(sys, "_androidworld_semantic_review_bootstrap", None) != prelock.get(
        "prelock_sha256"
    ):
        raise SemanticReviewError("semantic-review runner was not admitted by frozen bootstrap")
    if getattr(sys, "_androidworld_semantic_review_prelock_file_sha256", None) != sha256_file(
        prelock_path
    ):
        raise SemanticReviewError("bootstrap prelock physical hash differs")

    proposal_schema = load_json(proposal_schema_path, "proposal schema")
    body_schema = load_json(body_schema_path, "model output schema")
    checklist_schema = load_json(checklist_schema_path, "checklist schema")
    derived = model_body_schema(proposal_schema)
    if body_schema != derived:
        raise SemanticReviewError("prelocked model output schema is not derived from proposal schema")
    if schema_errors({}, proposal_schema) == [] or schema_errors({}, body_schema) == []:
        raise SemanticReviewError("review schemas unexpectedly accept an empty object")

    gate = prelock.get("canonical_output_gate")
    if not isinstance(gate, Mapping) or gate.get("promotion_authorized") is not False:
        raise SemanticReviewError("review output gate does not explicitly deny promotion")
    output_root = resolve_repo_path(gate.get("proposal_wave"), inside_candidate=True)
    if output_root != resolve_repo_path(config.get("output_root"), inside_candidate=True):
        raise SemanticReviewError("review config/prelock output roots differ")

    codex_info = prelock.get("codex_cli")
    if not isinstance(codex_info, Mapping) or codex_info.get("auth_mode") != "codex_login":
        raise SemanticReviewError("prelock does not prove Codex-login mode")
    invocation = Path(str(codex_info.get("invocation_path") or ""))
    codex_binary = Path(str(codex_info.get("binary_path") or "")).resolve()
    if not codex_binary.is_file() or sha256_file(codex_binary) != codex_info.get("binary_sha256"):
        raise SemanticReviewError("Codex binary differs from review prelock")
    current_invocation = shutil.which("codex")
    if (
        current_invocation is None
        or Path(os.path.abspath(current_invocation)) != invocation
        or invocation.resolve(strict=True) != codex_binary
        or codex_info.get("login_success_format") != EXACT_CODEX_LOGIN_STATUS
    ):
        raise SemanticReviewError("Codex invocation path/login contract differs")
    version = subprocess.run(
        [str(codex_binary), "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    login = subprocess.run(
        [str(codex_binary), "login", "status"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    login_detail = "\n".join(part.strip() for part in (login.stdout, login.stderr) if part.strip())
    if (
        version.returncode != 0
        or (version.stdout or version.stderr).strip() != codex_info.get("version")
        or login.returncode != 0
        or login_detail != EXACT_CODEX_LOGIN_STATUS
    ):
        raise SemanticReviewError(f"Codex login is inactive: {login_detail}")

    return ReviewContext(
        prelock_path=prelock_path,
        prelock=prelock,
        config_path=config_path,
        config=config,
        output_root=output_root,
        prompt_path=prompt_path,
        proposal_schema_path=proposal_schema_path,
        body_schema_path=body_schema_path,
        checklist_schema_path=checklist_schema_path,
        proposal_schema=proposal_schema,
        body_schema=body_schema,
        checklist_schema=checklist_schema,
        codex_binary=codex_binary,
        python_runtime=python_runtime,
    )


def verify_global_inputs(context: ReviewContext) -> None:
    """Recheck every byte binding; called before and after model work."""
    current = load_context(context.prelock_path)
    if current.prelock.get("prelock_sha256") != context.prelock.get("prelock_sha256"):
        raise SemanticReviewError("semantic-review prelock changed during generation")
    expected_tree = context.prelock.get("toolchain_exact_tree")
    snapshot_root = Path(
        str(context.prelock.get("toolchain_snapshot_root_absolute") or "")
    )
    if not isinstance(expected_tree, Mapping) or canonical_runtime_tree(snapshot_root) != dict(
        expected_tree
    ):
        raise SemanticReviewError("semantic-review toolchain exact tree changed")
    verify_python_runtime_trees(context.python_runtime)


def _recover_output(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        item = event.get("item")
        if not isinstance(item, Mapping) or item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if not isinstance(text, str):
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _input_paths(row: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    bindings = row["input_bindings"]
    return (
        verify_file_binding(bindings["packet"], f"{row['case_unit_id']} packet"),
        verify_file_binding(
            bindings["raw_checklist_yaml"], f"{row['case_unit_id']} raw checklist"
        ),
        verify_file_binding(bindings["issue_history"], f"{row['case_unit_id']} issue history"),
    )


def _command(context: ReviewContext, workspace: Path, output_path: Path) -> list[str]:
    return [
        str(context.codex_binary),
        "exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--model",
        str(context.config["model"]),
        "-c",
        f'model_reasoning_effort="{context.config["reasoning_effort"]}"',
        "-c",
        'model_verbosity="low"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(workspace / "review_output_schema.json"),
        "-o",
        str(output_path),
        "-",
    ]


def _child_environment(context: ReviewContext) -> dict[str, str]:
    environment = os.environ.copy()
    for variable in context.python_runtime.get("forbidden_child_python_environment") or []:
        environment.pop(str(variable), None)
    environment.update(
        {
            str(key): str(value)
            for key, value in (context.python_runtime.get("required_environment") or {}).items()
        }
    )
    if any(
        str(variable) in environment
        for variable in context.python_runtime.get("forbidden_child_python_environment") or []
    ):
        raise SemanticReviewError("forbidden Python environment escaped Codex child sanitization")
    return environment


def _terminate_process_group(process: subprocess.Popen[str], *, grace_seconds: float = 2.0) -> None:
    """Ensure the Codex process group has no surviving descendants."""
    pgid = process.pid
    def group_alive() -> bool:
        process.poll()
        try:
            os.killpg(pgid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError as exc:
            if process.returncode is not None:
                return False
            raise SemanticReviewError(f"cannot inspect Codex process group {pgid}: {exc}") from exc

    if not group_alive():
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not group_alive():
            return
        time.sleep(0.05)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not group_alive():
            return
        time.sleep(0.05)
    raise SemanticReviewError(f"Codex process group {pgid} survived SIGKILL")


def _write_attempt_failure(
    attempt_dir: Path,
    *,
    code: str,
    message: str,
    started_at: str,
    completed_at: str,
    returncode: int | None,
) -> None:
    payload = {
        "schema_version": "androidworld_semantic_review_attempt_failure/v1",
        "status": "failed",
        "code": code,
        "message": message,
        "started_at": started_at,
        "completed_at": completed_at,
        "returncode": returncode,
    }
    write_json_atomic(attempt_dir / "attempt_failure.json", add_self_hash(payload, "failure_sha256"))


def run_attempt(
    context: ReviewContext,
    row: Mapping[str, Any],
    attempt_index: int,
    attempt_dir: Path,
    concurrency: ProcessConcurrencyAudit,
) -> dict[str, Any]:
    case_id = str(row["case_unit_id"])
    task_id = str(row["task_id"])
    packet_path, checklist_path, issue_history_path = _input_paths(row)
    packet_text = packet_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")
    packet = parse_case_packet(packet_text)
    checklist = load_yaml_mapping(checklist_path, f"{case_id} raw checklist")
    issue_history = load_json(issue_history_path, f"{case_id} issue history")
    verify_issue_history(issue_history, case_id=case_id, rank=int(row["selection_rank"]))
    attempt_dir.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    started_monotonic = time.monotonic()

    with tempfile.TemporaryDirectory(prefix=f"androidworld-review-{case_id}-") as temporary:
        workspace = Path(temporary)
        (workspace / "review_instructions.md").write_bytes(context.prompt_path.read_bytes())
        (workspace / "case_packet.md").write_bytes(packet_path.read_bytes())
        (workspace / "raw_checklist.yaml").write_bytes(checklist_path.read_bytes())
        (workspace / "issue_history.json").write_bytes(issue_history_path.read_bytes())
        (workspace / "review_output_schema.json").write_bytes(context.body_schema_path.read_bytes())
        output_path = workspace / "model_output.json"
        command = _command(context, workspace, output_path)
        user_prompt = (
            "Independently review one AndroidWorld checklist. Read review_instructions.md, "
            "case_packet.md, raw_checklist.yaml, and issue_history.json completely. Use no other files or outside "
            "facts. Return exactly one JSON object conforming to review_output_schema.json. "
            "Do not modify files and do not claim final human acceptance."
        )
        process: subprocess.Popen[str] | None = None
        tracked = False
        timed_out = False
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
                env=_child_environment(context),
            )
            concurrency.start(case_id, attempt_index, process.pid)
            tracked = True
            try:
                stdout, stderr = process.communicate(
                    input=user_prompt,
                    timeout=int(context.config["codex_timeout_seconds"]),
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                _terminate_process_group(process)
                stdout, stderr = process.communicate()
            returncode: int | None = None if timed_out else process.returncode
        except OSError as exc:
            completed_at = utc_now()
            write_text_atomic(attempt_dir / "codex_events.jsonl", "")
            write_text_atomic(attempt_dir / "stderr.log", str(exc) + "\n")
            _write_attempt_failure(
                attempt_dir,
                code="codex_spawn_failed",
                message=str(exc),
                started_at=started_at,
                completed_at=completed_at,
                returncode=None,
            )
            return {"status": "failed", "code": "codex_spawn_failed", "message": str(exc)}
        finally:
            if process is not None:
                if process.poll() is None:
                    _terminate_process_group(process)
                    process.wait(timeout=5)
                else:
                    _terminate_process_group(process)
                if tracked:
                    concurrency.stop(case_id, attempt_index, process.pid)
        stdout = stdout or ""
        stderr = stderr or ""
        if timed_out:
            write_text_atomic(attempt_dir / "codex_events.jsonl", stdout)
            write_text_atomic(attempt_dir / "stderr.log", stderr)
            completed_at = utc_now()
            _write_attempt_failure(
                attempt_dir,
                code="codex_timeout",
                message=f"Codex timed out after {context.config['codex_timeout_seconds']} seconds",
                started_at=started_at,
                completed_at=completed_at,
                returncode=None,
            )
            return {"status": "failed", "code": "codex_timeout", "message": stderr}

        write_text_atomic(attempt_dir / "codex_events.jsonl", stdout)
        write_text_atomic(attempt_dir / "stderr.log", stderr)
        events, malformed = load_jsonl_events(stdout)
        if returncode != 0:
            completed_at = utc_now()
            message = stderr.strip() or stdout.strip() or "Codex returned no diagnostic"
            _write_attempt_failure(
                attempt_dir,
                code="codex_nonzero_exit",
                message=message,
                started_at=started_at,
                completed_at=completed_at,
                returncode=returncode,
            )
            return {"status": "failed", "code": "codex_nonzero_exit", "message": message}

        body: dict[str, Any] | None = None
        if output_path.is_file():
            try:
                candidate = json.loads(output_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                candidate = None
            if isinstance(candidate, dict):
                body = candidate
        if body is None:
            body = _recover_output(events)
        if body is None:
            completed_at = utc_now()
            _write_attempt_failure(
                attempt_dir,
                code="missing_structured_output",
                message="Codex completed without a structured review body",
                started_at=started_at,
                completed_at=completed_at,
                returncode=returncode,
            )
            return {"status": "failed", "code": "missing_structured_output", "message": ""}

        write_json_atomic(attempt_dir / "model_output.json", body)
        body_problems = validate_review_body(
            body,
            body_schema=context.body_schema,
            checklist=checklist,
            checklist_schema=context.checklist_schema,
            packet=packet,
            issue_history=issue_history,
        )
        response_id = event_response_id(events)
        completed_at = utc_now()
        if malformed:
            body_problems.append(f"Codex JSONL contained {len(malformed)} malformed event lines")
        if not response_id:
            body_problems.append("Codex JSONL has no thread.started response id")
        if body_problems:
            validation = {
                "schema_version": "androidworld_semantic_review_attempt_validation/v1",
                "status": "failed",
                "case_unit_id": case_id,
                "attempt_index": attempt_index,
                "issues": body_problems,
                "validated_at": completed_at,
            }
            write_json_atomic(
                attempt_dir / "validation.json", add_self_hash(validation, "validation_sha256")
            )
            _write_attempt_failure(
                attempt_dir,
                code="proposal_validation_failed",
                message="; ".join(body_problems),
                started_at=started_at,
                completed_at=completed_at,
                returncode=returncode,
            )
            return {
                "status": "failed",
                "code": "proposal_validation_failed",
                "message": "; ".join(body_problems),
            }

        assert response_id is not None
        prelock_binding = file_binding(context.prelock_path)
        review_configuration = {
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": context.config["model"],
            "model_version_claim": None,
            "model_version_evidence_note": (
                "Codex CLI does not expose an immutable backend model snapshot."
            ),
            "reasoning_effort": context.config["reasoning_effort"],
            "sandbox": "read-only",
            "independent_ephemeral_session": True,
            "prompt": file_binding(context.prompt_path),
            "proposal_schema": file_binding(context.proposal_schema_path),
            "model_output_schema_sha256": sha256_file(context.body_schema_path),
            "prelock": prelock_binding,
            "request_started_at": started_at,
            "response_completed_at": completed_at,
            "response_id": response_id,
        }
        proposal = build_proposal(
            case_id=case_id,
            task_id=task_id,
            input_bindings=row["input_bindings"],
            review_configuration=review_configuration,
            review_body=body,
        )
        proposal_problems = validate_proposal(
            proposal,
            proposal_schema=context.proposal_schema,
            body_schema=context.body_schema,
            checklist=checklist,
            checklist_schema=context.checklist_schema,
            packet=packet,
            issue_history=issue_history,
        )
        if proposal_problems:
            validation = {
                "schema_version": "androidworld_semantic_review_attempt_validation/v1",
                "status": "failed",
                "case_unit_id": case_id,
                "attempt_index": attempt_index,
                "issues": proposal_problems,
                "validated_at": completed_at,
            }
            write_json_atomic(
                attempt_dir / "validation.json", add_self_hash(validation, "validation_sha256")
            )
            _write_attempt_failure(
                attempt_dir,
                code="normalized_proposal_validation_failed",
                message="; ".join(proposal_problems),
                started_at=started_at,
                completed_at=completed_at,
                returncode=returncode,
            )
            return {
                "status": "failed",
                "code": "normalized_proposal_validation_failed",
                "message": "; ".join(proposal_problems),
            }

        write_json_atomic(attempt_dir / "proposal.json", proposal)
        fragments = reasoning_fragments(events)
        reasoning_text = "\n\n".join(fragments).strip()
        if not reasoning_text:
            reasoning_text = "No reasoning summary was emitted by Codex CLI."
        write_text_atomic(attempt_dir / "reasoning_summary.txt", reasoning_text + "\n")
        llm_call = {
            "schema_version": "androidworld_semantic_review_llm_call/v1",
            "phase": "independent_semantic_review_proposal",
            "case_unit_id": case_id,
            "task_id": task_id,
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": context.config["model"],
            "model_version_claim": None,
            "model_version_evidence_note": (
                "Codex CLI does not expose an immutable backend model snapshot."
            ),
            "reasoning_effort": context.config["reasoning_effort"],
            "sandbox": "read-only",
            "ephemeral": True,
            "ignore_user_config": True,
            "response_id": response_id,
            "request_started_at": started_at,
            "response_completed_at": completed_at,
            "duration_seconds": round(time.monotonic() - started_monotonic, 6),
            "attempt_index": attempt_index,
            "input_bindings": copy.deepcopy(row["input_bindings"]),
            "prompt": file_binding(context.prompt_path),
            "proposal_schema": file_binding(context.proposal_schema_path),
            "model_output_schema": file_binding(context.body_schema_path),
            "prelock": prelock_binding | {"prelock_sha256": context.prelock["prelock_sha256"]},
            "codex_binary": {
                "path": str(context.codex_binary),
                "sha256": sha256_file(context.codex_binary),
                "version": context.prelock["codex_cli"]["version"],
            },
            "token_usage": codex_usage(events),
            "command": command,
            "malformed_event_line_count": len(malformed),
            "promotion_authorized": False,
        }
        llm_call = add_self_hash(llm_call, "llm_call_sha256")
        write_json_atomic(attempt_dir / "llm_call.json", llm_call)
        validation = {
            "schema_version": "androidworld_semantic_review_attempt_validation/v1",
            "status": "passed",
            "case_unit_id": case_id,
            "task_id": task_id,
            "attempt_index": attempt_index,
            "proposal_status": body["proposal_status"],
            "issues": [],
            "validated_at": utc_now(),
            "promotion_authorized": False,
        }
        validation = add_self_hash(validation, "validation_sha256")
        write_json_atomic(attempt_dir / "validation.json", validation)
        receipt_files = {
            name: file_binding(attempt_dir / filename)
            for name, filename in (
                ("proposal", "proposal.json"),
                ("model_output", "model_output.json"),
                ("codex_events", "codex_events.jsonl"),
                ("stderr", "stderr.log"),
                ("reasoning_summary", "reasoning_summary.txt"),
                ("llm_call", "llm_call.json"),
                ("validation", "validation.json"),
            )
        }
        receipt = {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "status": "completed_valid_proposal",
            "case_unit_id": case_id,
            "task_id": task_id,
            "selection_rank": row["selection_rank"],
            "attempt_index": attempt_index,
            "proposal_status": body["proposal_status"],
            "files": receipt_files,
            "prelock_sha256": context.prelock["prelock_sha256"],
            "promotion_authorized": False,
        }
        receipt = add_self_hash(receipt, "receipt_sha256")
        write_json_atomic(attempt_dir / "receipt.json", receipt)
        return {
            "status": "completed",
            "proposal_status": body["proposal_status"],
            "receipt": receipt,
            "attempt_dir": attempt_dir,
        }


def verify_selected_result(
    context: ReviewContext, row: Mapping[str, Any], result_path: Path
) -> dict[str, Any]:
    result = load_json(result_path, f"{row['case_unit_id']} result")
    verify_self_hash(result, "result_sha256", f"{row['case_unit_id']} result")
    if (
        set(result)
        != {
            "schema_version",
            "status",
            "case_unit_id",
            "task_id",
            "selection_rank",
            "chosen_attempt",
            "proposal_status",
            "selected_receipt",
            "receipt_sha256",
            "prelock_sha256",
            "promotion_authorized",
            "result_sha256",
        }
        or
        result.get("schema_version") != "androidworld_semantic_review_case_result/v1"
        or result.get("status") != "completed"
        or result.get("case_unit_id") != row["case_unit_id"]
        or result.get("task_id") != row["task_id"]
        or result.get("promotion_authorized") is not False
        or result.get("prelock_sha256") != context.prelock["prelock_sha256"]
    ):
        raise SemanticReviewError(f"{row['case_unit_id']} selected result metadata is invalid")
    receipt_path = verify_file_binding(
        result.get("selected_receipt"), f"{row['case_unit_id']} receipt", inside_candidate=True
    )
    receipt = load_json(receipt_path, f"{row['case_unit_id']} receipt")
    verify_self_hash(receipt, "receipt_sha256", f"{row['case_unit_id']} receipt")
    if set(receipt) != {
        "schema_version",
        "status",
        "case_unit_id",
        "task_id",
        "selection_rank",
        "attempt_index",
        "proposal_status",
        "files",
        "prelock_sha256",
        "promotion_authorized",
        "receipt_sha256",
    }:
        raise SemanticReviewError(f"{row['case_unit_id']} receipt field set is not exact")
    expected_attempt_dir = (
        context.output_root
        / str(row["case_unit_id"])
        / "attempts"
        / f"attempt_{int(result.get('chosen_attempt') or 0):02d}"
    ).resolve()
    if receipt_path.parent != expected_attempt_dir or receipt_path.name != "receipt.json":
        raise SemanticReviewError(f"{row['case_unit_id']} receipt is not in its exact chosen attempt")
    expected_receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "status": "completed_valid_proposal",
        "case_unit_id": row["case_unit_id"],
        "task_id": row["task_id"],
        "selection_rank": row["selection_rank"],
        "attempt_index": result.get("chosen_attempt"),
        "proposal_status": result.get("proposal_status"),
        "prelock_sha256": context.prelock["prelock_sha256"],
        "promotion_authorized": False,
    }
    for key, expected in expected_receipt.items():
        if receipt.get(key) != expected:
            raise SemanticReviewError(
                f"{row['case_unit_id']} receipt {key}={receipt.get(key)!r}, expected {expected!r}"
            )
    if result.get("receipt_sha256") != receipt.get("receipt_sha256"):
        raise SemanticReviewError(f"{row['case_unit_id']} result/receipt hashes differ")
    expected_files = {
        "proposal",
        "model_output",
        "codex_events",
        "stderr",
        "reasoning_summary",
        "llm_call",
        "validation",
    }
    if set(receipt.get("files") or {}) != expected_files:
        raise SemanticReviewError(f"{row['case_unit_id']} receipt file set is incomplete")
    for name, binding in receipt["files"].items():
        verify_file_binding(binding, f"{row['case_unit_id']} receipt file {name}")
    proposal_path = verify_file_binding(
        receipt["files"]["proposal"], f"{row['case_unit_id']} proposal"
    )
    proposal = load_json(proposal_path, f"{row['case_unit_id']} proposal")
    model_output_path = verify_file_binding(
        receipt["files"]["model_output"], f"{row['case_unit_id']} model output"
    )
    model_output = load_json(model_output_path, f"{row['case_unit_id']} model output")
    if proposal.get("review") != model_output:
        raise SemanticReviewError(f"{row['case_unit_id']} normalized proposal alters model output")
    if proposal.get("input_bindings") != row.get("input_bindings"):
        raise SemanticReviewError(f"{row['case_unit_id']} proposal input bindings differ")
    proposal_config = proposal.get("review_configuration") or {}
    if (
        proposal_config.get("model") != context.config["model"]
        or proposal_config.get("reasoning_effort") != context.config["reasoning_effort"]
        or proposal_config.get("provider") != "codex_cli"
        or proposal_config.get("auth_mode") != "codex_login"
        or proposal_config.get("sandbox") != "read-only"
        or proposal_config.get("independent_ephemeral_session") is not True
        or proposal_config.get("model_version_claim") is not None
        or proposal_config.get("model_version_evidence_note")
        != "Codex CLI does not expose an immutable backend model snapshot."
        or (proposal_config.get("prelock") or {}).get("sha256") != sha256_file(context.prelock_path)
    ):
        raise SemanticReviewError(f"{row['case_unit_id']} proposal call binding differs")
    packet_path, checklist_path, issue_history_path = _input_paths(row)
    problems = validate_proposal(
        proposal,
        proposal_schema=context.proposal_schema,
        body_schema=context.body_schema,
        checklist=load_yaml_mapping(checklist_path),
        checklist_schema=context.checklist_schema,
        packet=parse_case_packet(packet_path.read_text(encoding="utf-8")),
        issue_history=load_json(issue_history_path, f"{row['case_unit_id']} issue history"),
    )
    if problems:
        raise SemanticReviewError(f"{row['case_unit_id']} selected proposal fails: {problems}")
    return result


def review_case(
    context: ReviewContext,
    row: Mapping[str, Any],
    resume: bool,
    concurrency: ProcessConcurrencyAudit,
) -> dict[str, Any]:
    case_id = str(row["case_unit_id"])
    case_dir = context.output_root / case_id
    result_path = case_dir / "result.json"
    if resume and result_path.is_file():
        existing_result = load_json(result_path, f"{case_id} existing result")
        if existing_result.get("status") == "completed":
            result = verify_selected_result(context, row, result_path)
            with PRINT_LOCK:
                print(f"[resume] {case_id}: {result['proposal_status']}", flush=True)
            return result
        history = case_dir / "failed_results"
        history.mkdir(exist_ok=True)
        history_path = history / f"result_{sha256_file(result_path)}.json"
        if history_path.exists():
            if sha256_file(history_path) != sha256_file(result_path):
                raise SemanticReviewError(f"{case_id} failed-result history hash collision")
            result_path.unlink()
        else:
            os.replace(result_path, history_path)
    if case_dir.exists():
        if not resume:
            raise SemanticReviewError(f"case output already exists without --resume: {case_dir}")
        # Failed/incomplete attempts are retained; choose the next unused attempt index.
    else:
        case_dir.mkdir(parents=True)
    attempts_root = case_dir / "attempts"
    attempts_root.mkdir(exist_ok=True)
    existing = [path for path in attempts_root.iterdir() if path.is_dir() and path.name.startswith("attempt_")]
    next_index = max([int(path.name.split("_")[-1]) for path in existing] or [0]) + 1
    failures: list[dict[str, Any]] = []
    max_attempts = int(context.config["max_attempts"])
    for offset in range(max_attempts):
        attempt_index = next_index + offset
        attempt_dir = attempts_root / f"attempt_{attempt_index:02d}"
        outcome = run_attempt(context, row, attempt_index, attempt_dir, concurrency)
        if outcome["status"] == "completed":
            receipt_path = outcome["attempt_dir"] / "receipt.json"
            result = {
                "schema_version": "androidworld_semantic_review_case_result/v1",
                "status": "completed",
                "case_unit_id": case_id,
                "task_id": row["task_id"],
                "selection_rank": row["selection_rank"],
                "chosen_attempt": attempt_index,
                "proposal_status": outcome["proposal_status"],
                "selected_receipt": file_binding(receipt_path),
                "receipt_sha256": outcome["receipt"]["receipt_sha256"],
                "prelock_sha256": context.prelock["prelock_sha256"],
                "promotion_authorized": False,
            }
            result = add_self_hash(result, "result_sha256")
            write_json_atomic(result_path, result)
            with PRINT_LOCK:
                print(f"[done] {case_id}: proposed {outcome['proposal_status']}", flush=True)
            return result
        failures.append(
            {"attempt_index": attempt_index, "code": outcome["code"], "message": outcome["message"]}
        )
        with PRINT_LOCK:
            print(f"[retry] {case_id} attempt {attempt_index}: {outcome['code']}", flush=True)
    result = {
        "schema_version": "androidworld_semantic_review_case_result/v1",
        "status": "failed",
        "case_unit_id": case_id,
        "task_id": row["task_id"],
        "selection_rank": row["selection_rank"],
        "attempt_failures": failures,
        "prelock_sha256": context.prelock["prelock_sha256"],
        "promotion_authorized": False,
    }
    result = add_self_hash(result, "result_sha256")
    write_json_atomic(result_path, result)
    return result


def run_self_test() -> int:
    source_schema = (
        WORK_ROOT / "schemas" / "androidworld_checklist_semantic_review_proposal.schema.json"
    )
    schema = load_json(source_schema, "source proposal schema")
    body = model_body_schema(schema)
    if schema_errors({}, body) == []:
        raise SemanticReviewError("derived model schema accepts empty output")
    full_packet_path = next(
        (WORK_ROOT / "case_packets" / "androidworld").glob("*/case_packet.md"), None
    )
    compact_packet_path = next(
        (WORK_ROOT / "case_packets" / "androidworld").glob("*/compact_case_packet.md"), None
    )
    if full_packet_path is None or compact_packet_path is None:
        raise SemanticReviewError("self-test cannot find full and compact packet samples")
    full = parse_case_packet(full_packet_path.read_text(encoding="utf-8"))
    compact = parse_case_packet(compact_packet_path.read_text(encoding="utf-8"))
    full_pointer = f"{full['canonical_support_path']}::$.case_unit_id"
    compact_pointer = f"{compact['canonical_support_path']}::$.identity.case_unit_id"
    from semantic_review_common import resolve_packet_pointer

    if not resolve_packet_pointer(full_pointer, full, review_level=True):
        raise SemanticReviewError("full-packet canonical JSON support did not resolve")
    if not resolve_packet_pointer(compact_pointer, compact, review_level=True):
        raise SemanticReviewError("compact-packet canonical JSON support did not resolve")
    print(
        json.dumps(
            {
                "status": "self_test_pass",
                "model_calls": 0,
                "writes": 0,
                "proposal_schema_sha256": sha256_file(source_schema),
                "model_body_schema_object_sha256": object_sha256(body),
                "full_packet_sample": repo_relative(full_packet_path),
                "compact_packet_sample": repo_relative(compact_packet_path),
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


def run_concurrency_self_test() -> int:
    order = [f"selftest_case_{index:03d}" for index in range(EXPECTED_CASE_COUNT)]
    observer_binary = Path("/bin/ps").resolve(strict=True)
    observer = {
        "invocation_path": "/bin/ps",
        "resolved_path": str(observer_binary),
        "sha256": sha256_file(observer_binary),
    }
    result: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(
        prefix="semantic_exact6_selftest_", dir=WORK_ROOT
    ) as temporary:
        root = Path(temporary)
        worker = root / "fake_codex_worker"
        worker.write_text(
            f"#!{sys.executable}\n"
            "import sys, time\n"
            "assert sys.argv[1] == 'exec'\n"
            "time.sleep(0.65)\n",
            encoding="utf-8",
        )
        worker.chmod(0o755)
        tracker = ProcessConcurrencyAudit(
            root / "positive",
            prelock_sha256="a" * 64,
            case_order=order,
            resume=False,
            process_observer=observer,
        )
        for offset in range(0, len(order), EXPECTED_PARALLELISM):
            processes: list[tuple[str, subprocess.Popen[str]]] = []
            try:
                for case_id in order[offset : offset + EXPECTED_PARALLELISM]:
                    process = subprocess.Popen(
                        [str(worker), "exec"],
                        text=True,
                        start_new_session=True,
                    )
                    tracker.start(case_id, 1, process.pid)
                    processes.append((case_id, process))
                for case_id, process in processes:
                    process.wait(timeout=5)
                    tracker.stop(case_id, 1, process.pid)
            finally:
                for _, process in processes:
                    if process.poll() is None:
                        _terminate_process_group(process)
                        process.wait(timeout=5)
        evidence = tracker.finalize()
        result["positive_exact6"] = (
            evidence["observed_peak_active_processes"] == EXPECTED_PARALLELISM
            and evidence["covered_case_count"] == EXPECTED_CASE_COUNT
        )
        original = tracker.events_path.read_text(encoding="utf-8")
        lines = original.splitlines()
        first = json.loads(lines[0])
        first["active_count"] = 99
        lines[0] = json.dumps(first, ensure_ascii=False, sort_keys=True)
        tracker.events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tamper_rejected = False
        try:
            verify_semantic_concurrency_evidence(
                events_path=tracker.events_path,
                audit_path=tracker.audit_path,
                expected_case_order=order,
                expected_prelock_sha256="a" * 64,
            )
        except SemanticReviewError:
            tamper_rejected = True
        finally:
            tracker.events_path.write_text(original, encoding="utf-8")
        result["tamper_rejected"] = tamper_rejected
    if not all(result.values()):
        raise SemanticReviewError(f"concurrency self-test failed: {result}")
    print(
        json.dumps(
            {"status": "self_test_pass", "model_calls": 0, **result},
            sort_keys=True,
            indent=2,
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.concurrency_self_test:
        return run_concurrency_self_test()
    if args.self_test:
        return run_self_test()
    if args.prelock is None:
        raise SemanticReviewError("--prelock is required unless --self-test is used")
    context = load_context(args.prelock)
    if context.output_root.exists() and not args.resume:
        raise SemanticReviewError(
            f"review output root already exists; use --resume only after inspection: {context.output_root}"
        )
    context.output_root.mkdir(parents=True, exist_ok=args.resume)
    old_summary = context.output_root / "_batch_summary.json"
    if args.resume and old_summary.is_file():
        history = context.output_root / "_history"
        history.mkdir(exist_ok=True)
        history_path = history / f"batch_summary_{sha256_file(old_summary)}.json"
        if history_path.exists():
            if sha256_file(history_path) != sha256_file(old_summary):
                raise SemanticReviewError("batch-summary history hash collision")
            old_summary.unlink()
        else:
            os.replace(old_summary, history_path)
    verify_global_inputs(context)
    rows = list(context.prelock["case_inputs"])
    concurrency = ProcessConcurrencyAudit(
        context.output_root / "_concurrency",
        prelock_sha256=context.prelock["prelock_sha256"],
        case_order=list(context.prelock["case_order"]),
        resume=args.resume,
        process_observer=context.python_runtime["process_observer"],
    )
    results: dict[str, dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=EXPECTED_PARALLELISM,
        thread_name_prefix="semantic-review",
    ) as executor:
        futures = {
            executor.submit(review_case, context, row, args.resume, concurrency): str(
                row["case_unit_id"]
            )
            for row in rows
        }
        for future in concurrent.futures.as_completed(futures):
            case_id = futures[future]
            try:
                results[case_id] = future.result()
            except Exception as exc:  # preserve other independent reviews
                results[case_id] = {
                    "schema_version": "androidworld_semantic_review_case_result/v1",
                    "status": "failed",
                    "case_unit_id": case_id,
                    "error": f"{type(exc).__name__}: {exc}",
                    "promotion_authorized": False,
                }
                with PRINT_LOCK:
                    print(f"[failed] {case_id}: {exc}", file=sys.stderr, flush=True)
    concurrency_evidence = concurrency.finalize()
    verify_global_inputs(context)
    ordered = [results[str(row["case_unit_id"])] for row in rows]
    completed = [row for row in ordered if row.get("status") == "completed"]
    proposed_accepted = [row for row in completed if row.get("proposal_status") == "accepted"]
    proposed_rejected = [row for row in completed if row.get("proposal_status") == "rejected"]
    summary_rows = []
    for row in ordered:
        item = {
            "case_unit_id": row.get("case_unit_id"),
            "status": row.get("status"),
            "proposal_status": row.get("proposal_status"),
            "promotion_authorized": False,
        }
        if row.get("status") == "completed":
            result_path = context.output_root / str(row["case_unit_id"]) / "result.json"
            item["result"] = file_binding(result_path)
            item["result_sha256"] = row.get("result_sha256")
            item["receipt_sha256"] = row.get("receipt_sha256")
        else:
            item["error"] = row.get("error") or row.get("attempt_failures")
        summary_rows.append(item)
    pass_batch = len(completed) == EXPECTED_CASE_COUNT
    summary = {
        "schema_version": "androidworld_semantic_review_batch_summary/v1",
        "status": "pass" if pass_batch else "fail",
        "review_id": context.prelock["review_id"],
        "source_generation_id": context.prelock["source_generation_id"],
        "generated_at": utc_now(),
        "case_count": EXPECTED_CASE_COUNT,
        "completed_count": len(completed),
        "failed_count": EXPECTED_CASE_COUNT - len(completed),
        "proposed_accepted_count": len(proposed_accepted),
        "proposed_rejected_count": len(proposed_rejected),
        "max_parallel": EXPECTED_PARALLELISM,
        "concurrency_evidence": concurrency_evidence,
        "prelock": file_binding(context.prelock_path)
        | {"prelock_sha256": context.prelock["prelock_sha256"]},
        "config": file_binding(context.config_path)
        | {"config_sha256": context.config["config_sha256"]},
        "cases": summary_rows,
        "review_authority": "model_proposals_only_root_agent_acceptance_required",
        "promotion_authorized": False,
    }
    summary = add_self_hash(summary, "batch_summary_sha256")
    write_json_atomic(context.output_root / "_batch_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if pass_batch else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
