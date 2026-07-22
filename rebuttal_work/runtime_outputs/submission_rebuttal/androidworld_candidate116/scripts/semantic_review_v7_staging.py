#!/usr/bin/env python3
"""Independent staged-workspace and anti-spoof receipt logic for review v7.

The raw-source paging implementation is reused as a byte-for-byte authority, but
this module has its own checklist reader, permission profile, prompt, workspace
manifest, combined ledger, and content bindings. It performs no model call.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

import wave004_v6_clean2_hardened_staging as source_staging

from semantic_review_v7_common import (
    SemanticReviewV7Error,
    canonical_bytes,
    canonical_sha256,
    checklist_semantic_inventory,
    is_exact_int,
    sha256_bytes,
    sha256_text,
)


PROFILE_NAME = "candidate_semantic_review_v7_isolated"
REVIEW_READER_BODY_PREFIX = "SEMANTIC_REVIEW_V7_READER_BODY "
REVIEW_READER_COMPLETION_PREFIX = "SEMANTIC_REVIEW_V7_READER_COMPLETE "
MAX_CHECKLIST_READER_BYTES = 96_000
MAX_CHECKLIST_READER_TOKENS = 28_000
MAX_STAGED_INPUT_TOKENS = 210_000
MAX_OUTPUT_RESERVE_TOKENS = 44_000
EFFECTIVE_CONTEXT_LIMIT = 258_400
DISABLED_CODEX_FEATURES = tuple(source_staging.DISABLED_CODEX_FEATURES)


class SemanticReviewV7StagingError(SemanticReviewV7Error):
    """Raised when staged review input or coverage proof is not exact."""


def _safe_relative(value: str) -> str:
    try:
        return source_staging.safe_source_path(value)
    except source_staging.StagingError as exc:
        raise SemanticReviewV7StagingError(str(exc)) from exc


def _write_new(path: Path, data: bytes, mode: int) -> dict[str, Any]:
    if path.is_symlink() or path.exists():
        raise SemanticReviewV7StagingError(
            f"staged path already exists/symlinked: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, mode)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return {
        "relative_path": "",
        "sha256": sha256_bytes(data),
        "size_bytes": len(data),
        "mode": mode,
    }


def _toml_key(value: Path | str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def build_permission_profile_override(
    *,
    workspace_root: Path,
    repository_root: Path,
    review_tmp_root: Path,
    auth_home: Path,
    original_codex_home: Path,
    isolated_home: Path,
    real_home: Path,
) -> str:
    return build_permission_profile_override_from_bound_paths(
        workspace_root=workspace_root,
        repository_root=repository_root,
        review_tmp_root=review_tmp_root,
        auth_home=auth_home,
        original_codex_home=original_codex_home,
        isolated_home=isolated_home,
        real_home=real_home,
        require_existing=True,
    )


def build_permission_profile_override_from_bound_paths(
    *,
    workspace_root: Path,
    repository_root: Path,
    review_tmp_root: Path,
    auth_home: Path,
    original_codex_home: Path,
    isolated_home: Path,
    real_home: Path,
    require_existing: bool,
) -> str:
    workspace = workspace_root.resolve(strict=require_existing)
    repository = repository_root.resolve(strict=require_existing)
    tmp_root = review_tmp_root.resolve(strict=require_existing)
    auth = auth_home.resolve(strict=require_existing)
    original_auth = original_codex_home.resolve(strict=require_existing)
    child_home = isolated_home.resolve(strict=require_existing)
    host_home = real_home.resolve(strict=require_existing)
    if workspace.parent != tmp_root:
        raise SemanticReviewV7StagingError(
            "case workspace is not an immediate child of the bound review TMP root"
        )
    if (
        len(
            {
                workspace,
                repository,
                tmp_root,
                auth,
                original_auth,
                child_home,
                host_home,
            }
        )
        != 7
    ):
        raise SemanticReviewV7StagingError("review permission roots are not distinct")
    if repository in workspace.parents or auth in workspace.parents:
        raise SemanticReviewV7StagingError(
            "review workspace is inside a denied authority root"
        )
    filesystem = (
        '{":minimal"="read",":workspace_roots"={"."="read"},'
        '":tmpdir"="deny",":slash_tmp"="deny",'
        + _toml_key(tmp_root)
        + '="deny",'
        + _toml_key(auth)
        + '="deny",'
        + _toml_key(original_auth)
        + '="deny",'
        + _toml_key(child_home)
        + '="deny",'
        + _toml_key(host_home)
        + '="deny",'
        + _toml_key(repository)
        + '="deny",'
        + _toml_key(workspace)
        + '="read"}'
    )
    return (
        "permissions."
        + PROFILE_NAME
        + '={description="Candidate116 semantic review v7 staged workspace read only",filesystem='
        + filesystem
        + ",network={enabled=false}}"
    )


def build_codex_exec_argv(
    *,
    codex_executable: Path,
    workspace_root: Path,
    model: str,
    reasoning_effort: str,
    repository_root: Path,
    review_tmp_root: Path,
    auth_home: Path,
    original_codex_home: Path,
    isolated_home: Path,
    real_home: Path,
) -> list[str]:
    workspace = workspace_root.resolve(strict=True)
    return build_codex_exec_argv_from_bound_paths(
        codex_executable=codex_executable,
        workspace_root=workspace,
        model=model,
        reasoning_effort=reasoning_effort,
        repository_root=repository_root,
        review_tmp_root=review_tmp_root,
        auth_home=auth_home,
        original_codex_home=original_codex_home,
        isolated_home=isolated_home,
        real_home=real_home,
        require_existing=True,
    )


def build_codex_exec_argv_from_bound_paths(
    *,
    codex_executable: Path,
    workspace_root: Path,
    model: str,
    reasoning_effort: str,
    repository_root: Path,
    review_tmp_root: Path,
    auth_home: Path,
    original_codex_home: Path,
    isolated_home: Path,
    real_home: Path,
    require_existing: bool,
) -> list[str]:
    workspace = workspace_root.resolve(strict=require_existing)
    schema_path = workspace / "output_schema.json"
    output_path = workspace / "review_body.json"
    profile = build_permission_profile_override_from_bound_paths(
        workspace_root=workspace,
        repository_root=repository_root,
        review_tmp_root=review_tmp_root,
        auth_home=auth_home,
        original_codex_home=original_codex_home,
        isolated_home=isolated_home,
        real_home=real_home,
        require_existing=require_existing,
    )
    codex = codex_executable.resolve(strict=True)
    command = [
        str(codex),
        "-a",
        "never",
        "--strict-config",
        "exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--model",
        model,
        "-c",
        f'default_permissions="{PROFILE_NAME}"',
        "-c",
        profile,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'model_verbosity="low"',
        "-c",
        'web_search="disabled"',
        "-c",
        "mcp_servers={}",
        "-c",
        'shell_environment_policy.inherit="none"',
    ]
    for feature in DISABLED_CODEX_FEATURES:
        command.extend(("--disable", feature))
    command.extend(
        (
            "--color",
            "never",
            "--json",
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
            "-",
        )
    )
    forbidden = {
        "--sandbox",
        "-s",
        "--add-dir",
        "--search",
        "--dangerously-bypass-approvals-and-sandbox",
    }
    if forbidden.intersection(command):
        raise SemanticReviewV7StagingError(
            "forbidden privilege/search flag entered review argv"
        )
    if command[:5] != [
        str(codex),
        "-a",
        "never",
        "--strict-config",
        "exec",
    ]:
        raise SemanticReviewV7StagingError(
            "global approval/strict-config flags are misplaced"
        )
    return command


def _checklist_argv(
    *, requirements_sha256: str, checklist_sha256: str, inventory_sha256: str
) -> list[str]:
    return [
        "/usr/bin/python3",
        "review_reader.py",
        "checklist",
        "--requirements-sha256",
        requirements_sha256,
        "--checklist-sha256",
        checklist_sha256,
        "--inventory-sha256",
        inventory_sha256,
    ]


def _review_reader_source() -> str:
    """Return a stdlib-only reader with an exact terminal body/argv proof."""

    return r"""#!/usr/bin/python3
import argparse
import hashlib
import json
import pathlib
import sys

BODY_PREFIX = "SEMANTIC_REVIEW_V7_READER_BODY "
COMPLETION_PREFIX = "SEMANTIC_REVIEW_V7_READER_COMPLETE "

def canonical_sha(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="command", required=True)
    read = sub.add_parser("checklist", add_help=False)
    read.add_argument("--requirements-sha256", required=True)
    read.add_argument("--checklist-sha256", required=True)
    read.add_argument("--inventory-sha256", required=True)
    args = parser.parse_args()
    if args.command != "checklist":
        raise SystemExit(2)
    manifest = json.loads(pathlib.Path("review_input_manifest.json").read_text(encoding="utf-8"))
    checklist = pathlib.Path("checklist.yaml").read_bytes()
    inventory_bytes = pathlib.Path("semantic_inventory.json").read_bytes()
    inventory = json.loads(inventory_bytes.decode("utf-8"))
    if (
        hashlib.sha256(checklist).hexdigest() != args.checklist_sha256
        or inventory.get("inventory_sha256") != args.inventory_sha256
        or manifest.get("requirements_sha256") != args.requirements_sha256
        or manifest.get("checklist_sha256") != args.checklist_sha256
        or manifest.get("inventory_sha256") != args.inventory_sha256
    ):
        raise SystemExit("SEMANTIC_REVIEW_V7_INPUT_BINDING_MISMATCH")
    argv = ["/usr/bin/python3", "review_reader.py", "checklist", "--requirements-sha256", args.requirements_sha256, "--checklist-sha256", args.checklist_sha256, "--inventory-sha256", args.inventory_sha256]
    identity = {
        "checklist_sha256": args.checklist_sha256,
        "inventory_sha256": args.inventory_sha256,
        "kind": "checklist",
        "requirements_sha256": args.requirements_sha256,
    }
    body = BODY_PREFIX + json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    body += "<<<BEGIN IMMUTABLE CHECKLIST YAML>>>\n" + checklist.decode("utf-8")
    if not body.endswith("\n"):
        body += "\n"
    body += "<<<END IMMUTABLE CHECKLIST YAML>>>\n"
    body += "<<<BEGIN EXPECTED SEMANTIC INVENTORY JSON>>>\n"
    body += json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    body += "<<<END EXPECTED SEMANTIC INVENTORY JSON>>>\n"
    completion = {
        "argv_sha256": canonical_sha(argv),
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "body_size_bytes": len(body.encode("utf-8")),
        "checklist_sha256": args.checklist_sha256,
        "inventory_sha256": args.inventory_sha256,
        "kind": "checklist",
        "requirements_sha256": args.requirements_sha256,
    }
    sys.stdout.write(body + COMPLETION_PREFIX + json.dumps(completion, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

if __name__ == "__main__":
    main()
"""


def render_checklist_output_for_audit(
    *,
    checklist_text: str,
    inventory: Mapping[str, Any],
    requirements_sha256: str,
) -> str:
    checklist_sha = sha256_text(checklist_text)
    inventory_sha = str(inventory.get("inventory_sha256") or "")
    argv = _checklist_argv(
        requirements_sha256=requirements_sha256,
        checklist_sha256=checklist_sha,
        inventory_sha256=inventory_sha,
    )
    identity = {
        "checklist_sha256": checklist_sha,
        "inventory_sha256": inventory_sha,
        "kind": "checklist",
        "requirements_sha256": requirements_sha256,
    }
    body = (
        REVIEW_READER_BODY_PREFIX
        + json.dumps(
            identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    )
    body += "<<<BEGIN IMMUTABLE CHECKLIST YAML>>>\n" + checklist_text
    if not body.endswith("\n"):
        body += "\n"
    body += "<<<END IMMUTABLE CHECKLIST YAML>>>\n"
    body += "<<<BEGIN EXPECTED SEMANTIC INVENTORY JSON>>>\n"
    body += json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    body += "<<<END EXPECTED SEMANTIC INVENTORY JSON>>>\n"
    completion = {
        "argv_sha256": canonical_sha256(argv),
        "body_sha256": sha256_text(body),
        "body_size_bytes": len(body.encode("utf-8")),
        "checklist_sha256": checklist_sha,
        "inventory_sha256": inventory_sha,
        "kind": "checklist",
        "requirements_sha256": requirements_sha256,
    }
    return (
        body
        + REVIEW_READER_COMPLETION_PREFIX
        + json.dumps(
            completion, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    )


def _packet_expectations_hash(operation_expectations: Mapping[str, Any]) -> str:
    for field in (
        "reader_operation_expectations_sha256",
        "operation_expectations_sha256",
        "expectations_sha256",
    ):
        value = operation_expectations.get(field)
        if isinstance(value, str) and len(value) == 64:
            return value
    raise SemanticReviewV7StagingError(
        "packet reader operation expectations lack one recognized self-hash"
    )


def build_review_operation_expectations(
    *,
    packet_operation_expectations: Mapping[str, Any],
    requirements: Mapping[str, Any],
    checklist_text: str,
    inventory: Mapping[str, Any],
    expected_final_body: Mapping[str, Any],
    token_counter: Callable[[str], int],
) -> dict[str, Any]:
    """Extend frozen packet A+B with exactly one terminal checklist operation."""

    try:
        source_staging.verify_reader_operation_expectations_binding(
            requirements, packet_operation_expectations
        )
    except source_staging.StagingError as exc:
        raise SemanticReviewV7StagingError(str(exc)) from exc
    requirements_sha = str(requirements.get("requirements_sha256") or "")
    packet_expectations_sha = _packet_expectations_hash(packet_operation_expectations)
    checklist_sha = sha256_text(checklist_text)
    inventory_sha = str(inventory.get("inventory_sha256") or "")
    argv = _checklist_argv(
        requirements_sha256=requirements_sha,
        checklist_sha256=checklist_sha,
        inventory_sha256=inventory_sha,
    )
    output = render_checklist_output_for_audit(
        checklist_text=checklist_text,
        inventory=inventory,
        requirements_sha256=requirements_sha,
    )
    packet_operations = list(packet_operation_expectations.get("operations") or [])
    if not packet_operations:
        raise SemanticReviewV7StagingError("packet reader B has no ordered operations")
    semantic_command = " ".join(argv)
    event_command = source_staging.render_codex_event_command(argv)
    checklist_operation = {
        "operation_index": len(packet_operations),
        "operation_id": "review_checklist",
        "kind": "checklist",
        "ordinal_after_packet_operations": True,
        "argv": argv,
        "argv_sha256": canonical_sha256(argv),
        "semantic_command": semantic_command,
        "exact_command": event_command,
        "event_command_sha256": sha256_text(event_command),
        "expected_output_sha256": sha256_text(output),
        "expected_output_size_bytes": len(output.encode("utf-8")),
        "expected_output_o200k_tokens": token_counter(output),
        "checklist_sha256": checklist_sha,
        "inventory_sha256": inventory_sha,
        "requirements_sha256": requirements_sha,
    }
    checklist_operation["operation_sha256"] = canonical_sha256(checklist_operation)
    if (
        checklist_operation["expected_output_size_bytes"] > MAX_CHECKLIST_READER_BYTES
        or checklist_operation["expected_output_o200k_tokens"]
        > MAX_CHECKLIST_READER_TOKENS
    ):
        raise SemanticReviewV7StagingError(
            "review checklist operation exceeds hard envelope"
        )
    packet_operation_ids = [
        f"packet_{index:04d}_{row.get('kind')}:{row.get('operation_sha256')}"
        for index, row in enumerate(packet_operations)
    ]
    if any(
        not is_exact_int(row.get("operation_index"), expected=index)
        or not isinstance(row.get("kind"), str)
        or not isinstance(row.get("operation_sha256"), str)
        or len(row["operation_sha256"]) != 64
        for index, row in enumerate(packet_operations)
    ):
        raise SemanticReviewV7StagingError(
            "packet reader B operation identities are malformed"
        )
    payload = {
        "schema_version": "androidworld_candidate116_semantic_review_v7_reader_operation_expectations/v1",
        "production_namespace": packet_operation_expectations.get(
            "production_namespace"
        ),
        "case_unit_id": requirements.get("case_unit_id"),
        "requirements_sha256": requirements_sha,
        "packet_reader_operation_expectations_sha256": packet_expectations_sha,
        "packet_operation_count": len(packet_operations),
        "packet_operation_ids": packet_operation_ids,
        "packet_operations_sha256": packet_operation_expectations.get(
            "operations_sha256"
        ),
        "event_trust_policy": source_staging.exact_event_trust_policy(),
        "event_shell_carrier": source_staging.codex_event_shell_carrier_binding(),
        "checklist_operation": checklist_operation,
        "combined_operation_count": len(packet_operations) + 1,
        "combined_operation_ids": [*packet_operation_ids, "review_checklist"],
        "global_order": "all_frozen_packet_operations_then_one_review_checklist_operation",
        "additional_operations_allowed": False,
    }
    payload["review_operation_expectations_sha256"] = canonical_sha256(payload)
    return payload


def materialize_review_workspace(
    *,
    workspace_root: Path,
    case_packet_text: str,
    checklist_text: str,
    checklist: Mapping[str, Any],
    output_schema: Mapping[str, Any],
    token_counter: Callable[[str], int],
    tokenizer_binding: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        workspace_root.is_symlink()
        or not workspace_root.is_dir()
        or any(workspace_root.iterdir())
    ):
        raise SemanticReviewV7StagingError(
            "review workspace must be a new empty directory"
        )
    try:
        parsed = source_staging.parse_packet_sources(case_packet_text)
        requirements = source_staging.build_coverage_requirements(
            parsed, token_counter=token_counter, tokenizer_binding=tokenizer_binding
        )
    except source_staging.StagingError as exc:
        raise SemanticReviewV7StagingError(str(exc)) from exc
    requirements["case_packet_sha256"] = sha256_text(case_packet_text)
    requirements["source_inventory"] = [
        {
            key: parsed["sources"][path][key]
            for key in ("path", "sha256", "size_bytes", "line_count")
        }
        for path in parsed["inventory"]
    ]
    requirements.pop("requirements_sha256", None)
    requirements["requirements_sha256"] = canonical_sha256(requirements)
    claimed_requirements_sha = requirements.get("requirements_sha256")
    requirements_core = dict(requirements)
    requirements_core.pop("requirements_sha256", None)
    if claimed_requirements_sha != canonical_sha256(requirements_core):
        raise SemanticReviewV7StagingError(
            "coverage requirements A self-hash is invalid"
        )
    inventory = checklist_semantic_inventory(checklist)
    build_packet_expectations = getattr(
        source_staging, "build_reader_operation_expectations", None
    )
    if not callable(build_packet_expectations):
        raise SemanticReviewV7StagingError(
            "hardened staging lacks finalized A+B reader operation expectations interface"
        )
    packet_operation_expectations = build_packet_expectations(
        case_packet_text=case_packet_text,
        parsed=parsed,
        requirements=requirements,
        token_counter=token_counter,
    )
    try:
        source_staging.verify_reader_operation_expectations_binding(
            requirements, packet_operation_expectations
        )
    except source_staging.StagingError as exc:
        raise SemanticReviewV7StagingError(str(exc)) from exc
    review_operation_expectations = build_review_operation_expectations(
        packet_operation_expectations=packet_operation_expectations,
        requirements=requirements,
        checklist_text=checklist_text,
        inventory=inventory,
        token_counter=token_counter,
    )
    checklist_sha = sha256_text(checklist_text)
    checklist_output = render_checklist_output_for_audit(
        checklist_text=checklist_text,
        inventory=inventory,
        requirements_sha256=requirements["requirements_sha256"],
    )
    checklist_tokens = token_counter(checklist_output)
    if (
        len(checklist_output.encode("utf-8")) > MAX_CHECKLIST_READER_BYTES
        or checklist_tokens > MAX_CHECKLIST_READER_TOKENS
    ):
        raise SemanticReviewV7StagingError(
            "checklist/inventory reader envelope exceeds hard limit"
        )

    files: list[dict[str, Any]] = []

    def write(relative: str, data: bytes, mode: int = 0o444) -> None:
        row = _write_new(
            workspace_root / PurePosixPath(_safe_relative(relative)), data, mode
        )
        row["relative_path"] = relative
        files.append(row)

    write("case_packet.md", case_packet_text.encode("utf-8"))
    for source_path in parsed["inventory"]:
        write(
            f"packet_sources/{source_path}",
            parsed["sources"][source_path]["text"].encode("utf-8"),
        )
    write(
        "source_inventory_manifest.json",
        (
            json.dumps(
                {
                    "schema_version": "androidworld_candidate116_semantic_review_v7_source_inventory/v1",
                    "case_unit_id": requirements["case_unit_id"],
                    "source_order": parsed["inventory"],
                    "sources": [
                        {
                            key: parsed["sources"][path][key]
                            for key in (
                                "path",
                                "source_ref",
                                "language",
                                "sha256",
                                "size_bytes",
                                "line_count",
                            )
                        }
                        for path in parsed["inventory"]
                    ],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
    )
    write(
        "model_input_coverage.json",
        (
            json.dumps(requirements, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8"),
    )
    write("packet_reader.py", source_staging._reader_source().encode("utf-8"))
    write("checklist.yaml", checklist_text.encode("utf-8"))
    write(
        "semantic_inventory.json",
        (
            json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    )
    review_input = {
        "schema_version": "androidworld_candidate116_semantic_review_v7_staged_input/v1",
        "case_unit_id": requirements["case_unit_id"],
        "task_id": requirements["task_id"],
        "case_packet_sha256": sha256_text(case_packet_text),
        "requirements_sha256": requirements["requirements_sha256"],
        "checklist_sha256": checklist_sha,
        "inventory_sha256": inventory["inventory_sha256"],
        "packet_reader_operation_expectations_sha256": _packet_expectations_hash(
            packet_operation_expectations
        ),
        "review_operation_expectations_sha256": review_operation_expectations[
            "review_operation_expectations_sha256"
        ],
    }
    review_input["staged_input_sha256"] = canonical_sha256(review_input)
    write(
        "review_input_manifest.json",
        (
            json.dumps(review_input, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8"),
    )
    write("review_reader.py", _review_reader_source().encode("utf-8"))
    write(
        "packet_reader_operation_expectations.json",
        (
            json.dumps(
                packet_operation_expectations,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
    )
    write(
        "review_operation_expectations.json",
        (
            json.dumps(
                review_operation_expectations,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
    )
    write(
        "output_schema.json",
        (
            json.dumps(output_schema, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8"),
    )
    write("review_body.json", b"", 0o600)
    files.sort(key=lambda row: row["relative_path"])
    manifest = {
        "schema_version": "androidworld_candidate116_semantic_review_v7_materialization/v1",
        "case_unit_id": requirements["case_unit_id"],
        "task_id": requirements["task_id"],
        "requirements_sha256": requirements["requirements_sha256"],
        "checklist_sha256": checklist_sha,
        "inventory_sha256": inventory["inventory_sha256"],
        "packet_reader_operation_expectations_sha256": _packet_expectations_hash(
            packet_operation_expectations
        ),
        "review_operation_expectations_sha256": review_operation_expectations[
            "review_operation_expectations_sha256"
        ],
        "input_files": [
            row for row in files if row["relative_path"] != "review_body.json"
        ],
        "output_file": next(
            row for row in files if row["relative_path"] == "review_body.json"
        ),
        "allowed_namespace": sorted(
            [row["relative_path"] for row in files] + ["workspace_materialization.json"]
        ),
        "raw_source_count": len(parsed["inventory"]),
        "checklist_reader_envelope_bytes": len(checklist_output.encode("utf-8")),
        "checklist_reader_envelope_o200k_tokens": checklist_tokens,
        "coverage_requirements": requirements,
        "packet_reader_operation_expectations": packet_operation_expectations,
        "review_operation_expectations": review_operation_expectations,
        "semantic_inventory": inventory,
        "raw_sources": {
            path: {
                "sha256": parsed["sources"][path]["sha256"],
                "line_count": parsed["sources"][path]["line_count"],
            }
            for path in parsed["inventory"]
        },
    }
    manifest["materialization_sha256"] = canonical_sha256(manifest)
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _write_new(workspace_root / "workspace_materialization.json", manifest_bytes, 0o444)
    manifest["workspace_manifest_file_sha256"] = sha256_bytes(manifest_bytes)
    seal_review_workspace(workspace_root, manifest)
    return manifest


def seal_review_workspace(workspace_root: Path, manifest: Mapping[str, Any]) -> None:
    for row in manifest["input_files"]:
        os.chmod(workspace_root / row["relative_path"], 0o444)
    os.chmod(workspace_root / "workspace_materialization.json", 0o444)
    os.chmod(workspace_root / "review_body.json", 0o600)
    for path in sorted(
        (item for item in workspace_root.rglob("*") if item.is_dir()),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        os.chmod(path, 0o555)
    os.chmod(workspace_root, 0o555)


def verify_review_workspace(
    workspace_root: Path, manifest: Mapping[str, Any], *, require_output: bool
) -> None:
    observed: set[str] = set()
    for path in workspace_root.rglob("*"):
        if path.is_symlink():
            raise SemanticReviewV7StagingError(
                f"symlink appeared in review workspace: {path}"
            )
        if path.is_file():
            observed.add(path.relative_to(workspace_root).as_posix())
    if observed != set(manifest["allowed_namespace"]):
        raise SemanticReviewV7StagingError(
            f"review workspace namespace changed: {sorted(observed ^ set(manifest['allowed_namespace']))}"
        )
    for row in manifest["input_files"]:
        path = workspace_root / row["relative_path"]
        if (
            sha256_bytes(path.read_bytes()) != row["sha256"]
            or path.stat().st_size != row["size_bytes"]
            or stat.S_IMODE(path.stat().st_mode) != 0o444
        ):
            raise SemanticReviewV7StagingError(
                f"staged input changed: {row['relative_path']}"
            )
    materialization_path = workspace_root / "workspace_materialization.json"
    if (
        sha256_bytes(materialization_path.read_bytes())
        != manifest["workspace_manifest_file_sha256"]
    ):
        raise SemanticReviewV7StagingError("workspace materialization file changed")
    output = workspace_root / "review_body.json"
    if require_output and output.stat().st_size == 0:
        raise SemanticReviewV7StagingError("Codex did not write review_body.json")


def unseal_for_cleanup(workspace_root: Path) -> None:
    for path in sorted(
        (item for item in workspace_root.rglob("*") if item.is_dir()),
        key=lambda item: len(item.parts),
    ):
        os.chmod(path, 0o700)
    os.chmod(workspace_root, 0o700)
    for path in workspace_root.rglob("*"):
        if path.is_file():
            os.chmod(path, 0o600)


def staged_review_prompt(*, base_prompt: str, manifest: Mapping[str, Any]) -> str:
    requirements = manifest["coverage_requirements"]
    checklist_command = " ".join(
        _checklist_argv(
            requirements_sha256=requirements["requirements_sha256"],
            checklist_sha256=manifest["checklist_sha256"],
            inventory_sha256=manifest["inventory_sha256"],
        )
    )
    return (
        base_prompt.rstrip()
        + "\n\n## Bound case-specific execution values\n\n"
        + f"Case: `{manifest['case_unit_id']}` / task `{manifest['task_id']}`.\n"
        + f"Coverage requirements SHA-256: `{requirements['requirements_sha256']}`.\n"
        + f"Coverage plan pages: `{requirements['coverage_page_count']}`.\n"
        + f"Coverage raw ranges: `{requirements['required_range_count']}`.\n"
        + "Packet reader operation expectations SHA-256: `"
        + str(manifest["packet_reader_operation_expectations_sha256"])
        + "`.\n"
        + "Exact packet reader operation count: `"
        + str(manifest["packet_reader_operation_expectations"]["operation_count"])
        + "`.\n"
        + "Review operation expectations SHA-256: `"
        + str(manifest["review_operation_expectations_sha256"])
        + "`.\n"
        + "After all packet-reader ranges, run this exact final checklist command once:\n\n"
        + f"`{checklist_command}`\n"
    )


def _verify_checklist_envelope(
    *,
    output: str,
    argv: Sequence[str],
    checklist_sha256: str,
    inventory_sha256: str,
    requirements_sha256: str,
) -> dict[str, Any]:
    if not output.endswith("\n"):
        raise SemanticReviewV7StagingError(
            "checklist reader output lacks terminal newline"
        )
    marker_start = output.rfind("\n" + REVIEW_READER_COMPLETION_PREFIX)
    if marker_start < 0:
        raise SemanticReviewV7StagingError("checklist reader terminal marker is absent")
    body = output[: marker_start + 1]
    marker_line = output[marker_start + 1 : -1]
    if REVIEW_READER_COMPLETION_PREFIX in body or "\n" in marker_line:
        raise SemanticReviewV7StagingError(
            "checklist reader marker is duplicated/nonterminal"
        )
    try:
        completion = json.loads(marker_line[len(REVIEW_READER_COMPLETION_PREFIX) :])
    except json.JSONDecodeError as exc:
        raise SemanticReviewV7StagingError(
            "checklist reader completion JSON is invalid"
        ) from exc
    expected = {
        "argv_sha256": canonical_sha256(list(argv)),
        "body_sha256": sha256_text(body),
        "body_size_bytes": len(body.encode("utf-8")),
        "checklist_sha256": checklist_sha256,
        "inventory_sha256": inventory_sha256,
        "kind": "checklist",
        "requirements_sha256": requirements_sha256,
    }
    if canonical_bytes(completion) != canonical_bytes(expected):
        raise SemanticReviewV7StagingError(
            "checklist reader completion does not bind exact body/argv/inputs"
        )
    return completion


def verify_codex_0144_event_framing(
    events: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    """Validate the exact observed Codex 0.144.4 JSONL outer event shape."""

    if len(events) < 5:
        raise SemanticReviewV7StagingError("Codex event ledger is too short")
    thread_event = events[0]
    turn_started = events[1]
    final_agent_event = events[-2]
    turn_completed = events[-1]
    if (
        set(thread_event) != {"type", "thread_id"}
        or thread_event.get("type") != "thread.started"
        or not isinstance(thread_event.get("thread_id"), str)
        or not thread_event["thread_id"]
        or set(turn_started) != {"type"}
        or turn_started.get("type") != "turn.started"
        or set(final_agent_event) != {"type", "item"}
        or final_agent_event.get("type") != "item.completed"
        or not isinstance(final_agent_event.get("item"), Mapping)
    ):
        raise SemanticReviewV7StagingError(
            "Codex thread/turn/final-agent framing is not exact"
        )
    final_agent = final_agent_event["item"]
    if (
        set(final_agent) != {"id", "type", "text"}
        or final_agent.get("type") != "agent_message"
        or not isinstance(final_agent.get("id"), str)
        or not final_agent["id"]
        or not isinstance(final_agent.get("text"), str)
        or final_agent["text"] != final_agent["text"].strip()
    ):
        raise SemanticReviewV7StagingError(
            "final Codex agent item is not exact id/type/text JSON"
        )
    try:
        final_body = json.loads(final_agent["text"])
    except json.JSONDecodeError as exc:
        raise SemanticReviewV7StagingError(
            "final Codex agent text is not one JSON value"
        ) from exc
    if not isinstance(final_body, Mapping):
        raise SemanticReviewV7StagingError(
            "final Codex agent JSON is not an object"
        )

    required_usage = {
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    }
    usage = turn_completed.get("usage")
    if (
        set(turn_completed) != {"type", "usage"}
        or turn_completed.get("type") != "turn.completed"
        or not isinstance(usage, Mapping)
        or set(usage) != required_usage
        or any(
            not is_exact_int(usage.get(field), minimum=0) for field in required_usage
        )
        or usage["cached_input_tokens"] > usage["input_tokens"]
        or usage["reasoning_output_tokens"] > usage["output_tokens"]
    ):
        raise SemanticReviewV7StagingError(
            "terminal turn.completed usage is not the exact four-field 0.144.4 shape"
        )

    active: tuple[str, str] | None = None
    seen_command_ids: set[str] = set()
    reasoning_event_count = 0
    command_count = 0
    command_item_keys = {
        "aggregated_output",
        "command",
        "exit_code",
        "id",
        "status",
        "type",
    }
    for event in events[2:-2]:
        if set(event) != {"type", "item"} or not isinstance(
            event.get("item"), Mapping
        ):
            raise SemanticReviewV7StagingError(
                "non-exact event appears inside the Codex item sequence"
            )
        item = event["item"]
        if item.get("type") == "reasoning":
            if (
                set(item) != {"id", "type", "text"}
                or event.get("type") not in {"item.started", "item.completed"}
                or not isinstance(item.get("id"), str)
                or not item["id"]
                or not isinstance(item.get("text"), str)
                or active is not None
            ):
                raise SemanticReviewV7StagingError(
                    "reasoning item shape/order is not exact"
                )
            reasoning_event_count += 1
            continue
        if set(item) != command_item_keys or item.get("type") != "command_execution":
            raise SemanticReviewV7StagingError(
                "non-command/intermediate agent item appears before final JSON"
            )
        item_id = item.get("id")
        command = item.get("command")
        if (
            not isinstance(item_id, str)
            or not item_id
            or not isinstance(command, str)
            or not command
        ):
            raise SemanticReviewV7StagingError(
                "command event lacks one stable id/exact command"
            )
        if event.get("type") == "item.started":
            if (
                active is not None
                or item_id in seen_command_ids
                or item.get("status") != "in_progress"
                or item.get("exit_code") is not None
                or item.get("aggregated_output") != ""
            ):
                raise SemanticReviewV7StagingError(
                    "command start shape/status/order is not exact"
                )
            seen_command_ids.add(item_id)
            active = (item_id, command)
            continue
        if (
            event.get("type") != "item.completed"
            or active != (item_id, command)
            or item.get("status") != "completed"
            or not is_exact_int(item.get("exit_code"), expected=0)
            or not isinstance(item.get("aggregated_output"), str)
        ):
            raise SemanticReviewV7StagingError(
                "command completion shape/status/same-id pair is not exact"
            )
        command_count += 1
        active = None
    if active is not None or command_count < 1 or command_count != len(
        seen_command_ids
    ):
        raise SemanticReviewV7StagingError(
            "Codex command sequence has an incomplete/duplicate pair"
        )
    audit = {
        "schema_version": "androidworld_candidate116_semantic_review_v7_codex_0144_event_framing/v1",
        "status": "exact_thread_turn_items_final_agent_and_four_field_usage",
        "thread_id": thread_event["thread_id"],
        "command_count": command_count,
        "reasoning_event_count": reasoning_event_count,
        "terminal_agent_message_id": final_agent["id"],
        "terminal_agent_message_text_sha256": sha256_text(final_agent["text"]),
        "terminal_agent_message_body_sha256": canonical_sha256(final_body),
        "usage": dict(usage),
        "total_tokens_field_present": False,
    }
    audit["event_framing_sha256"] = canonical_sha256(audit)
    return audit, final_body


def combined_coverage_receipt_from_events(
    *,
    events: list[dict[str, Any]],
    requirements: Mapping[str, Any],
    packet_operation_expectations: Mapping[str, Any],
    review_operation_expectations: Mapping[str, Any],
    checklist_text: str,
    inventory: Mapping[str, Any],
    token_counter: Callable[[str], int],
) -> dict[str, Any]:
    """Verify one global source-then-checklist ledger from same-ID completions only."""

    event_framing, final_body = verify_codex_0144_event_framing(events)
    if canonical_bytes(final_body) != canonical_bytes(expected_final_body):
        raise SemanticReviewV7StagingError(
            "final Codex agent JSON differs from the bound structured output body"
        )

    try:
        records = source_staging.ordered_completed_command_records(events)
    except source_staging.StagingError as exc:
        raise SemanticReviewV7StagingError(str(exc)) from exc
    try:
        source_staging.verify_reader_operation_expectations_binding(
            requirements, packet_operation_expectations
        )
    except source_staging.StagingError as exc:
        raise SemanticReviewV7StagingError(str(exc)) from exc
    expected_review = build_review_operation_expectations(
        packet_operation_expectations=packet_operation_expectations,
        requirements=requirements,
        checklist_text=checklist_text,
        inventory=inventory,
        token_counter=token_counter,
    )
    if canonical_bytes(dict(review_operation_expectations)) != canonical_bytes(
        expected_review
    ):
        raise SemanticReviewV7StagingError(
            "review-layer operation expectations differ from exact recomputation"
        )
    claimed_review_sha = expected_review["review_operation_expectations_sha256"]
    source_count = packet_operation_expectations.get("operation_count")
    if not is_exact_int(
        source_count, expected=len(packet_operation_expectations["operations"])
    ):
        raise SemanticReviewV7StagingError(
            "packet operation count is not an exact integer"
        )
    if len(records) != source_count + 1:
        raise SemanticReviewV7StagingError(
            "global review command ledger is not exact source coverage plus one checklist read"
        )
    source_ids = {record["id"] for record in records[:source_count]}
    source_events = [
        event
        for event in events
        if not isinstance(event.get("item"), Mapping)
        or event["item"].get("type") != "command_execution"
        or event["item"].get("id") in source_ids
    ]
    try:
        source_receipt = source_staging.coverage_receipt_from_events(
            source_events, requirements, packet_operation_expectations
        )
        source_staging.verify_coverage_receipt_against_events(
            source_receipt,
            source_events,
            requirements,
            packet_operation_expectations,
        )
    except source_staging.StagingError as exc:
        raise SemanticReviewV7StagingError(str(exc)) from exc

    checklist_sha = sha256_text(checklist_text)
    inventory_sha = str(inventory.get("inventory_sha256") or "")
    requirements_sha = str(requirements.get("requirements_sha256") or "")
    expected_argv = _checklist_argv(
        requirements_sha256=requirements_sha,
        checklist_sha256=checklist_sha,
        inventory_sha256=inventory_sha,
    )
    final = records[-1]
    expected_semantic_command = " ".join(expected_argv)
    expected_event_command = source_staging.render_codex_event_command(expected_argv)
    if final["command"] != expected_event_command:
        raise SemanticReviewV7StagingError(
            "final global ledger command is not the one exact checklist reader"
        )
    expected_output = render_checklist_output_for_audit(
        checklist_text=checklist_text,
        inventory=inventory,
        requirements_sha256=requirements_sha,
    )
    frozen_checklist_operation = review_operation_expectations.get(
        "checklist_operation"
    )
    if (
        not isinstance(frozen_checklist_operation, Mapping)
        or frozen_checklist_operation.get("argv") != expected_argv
        or frozen_checklist_operation.get("argv_sha256")
        != canonical_sha256(expected_argv)
        or frozen_checklist_operation.get("semantic_command")
        != expected_semantic_command
        or frozen_checklist_operation.get("exact_command") != expected_event_command
        or frozen_checklist_operation.get("event_command_sha256")
        != sha256_text(expected_event_command)
        or frozen_checklist_operation.get("expected_output_sha256")
        != sha256_text(expected_output)
        or frozen_checklist_operation.get("expected_output_size_bytes")
        != len(expected_output.encode("utf-8"))
    ):
        raise SemanticReviewV7StagingError(
            "frozen review-layer checklist operation differs from exact recomputation"
        )
    if final["output"] != expected_output:
        raise SemanticReviewV7StagingError(
            "checklist same-ID completed output differs from exact frozen envelope"
        )
    completion = _verify_checklist_envelope(
        output=final["output"],
        argv=expected_argv,
        checklist_sha256=checklist_sha,
        inventory_sha256=inventory_sha,
        requirements_sha256=requirements_sha,
    )
    if len(final["output"].encode("utf-8")) > MAX_CHECKLIST_READER_BYTES:
        raise SemanticReviewV7StagingError(
            "checklist reader output exceeds byte hard limit"
        )

    forbidden_item_types = {
        "mcp_tool_call",
        "web_search",
        "file_change",
        "computer_use",
        "image_generation",
        "tool_call",
    }
    for event in events:
        item = event.get("item")
        if isinstance(item, Mapping) and item.get("type") in forbidden_item_types:
            raise SemanticReviewV7StagingError(
                f"forbidden non-reader tool event appeared: {item.get('type')}"
            )

    payload = {
        "schema_version": "androidworld_candidate116_semantic_review_v7_combined_coverage/v1",
        "status": "all_raw_official_then_immutable_checklist_read_with_paired_terminal_envelopes",
        "case_unit_id": requirements.get("case_unit_id"),
        "requirements_sha256": requirements_sha,
        "packet_reader_operation_expectations_sha256": _packet_expectations_hash(
            packet_operation_expectations
        ),
        "review_operation_expectations_sha256": claimed_review_sha,
        "checklist_sha256": checklist_sha,
        "inventory_sha256": inventory_sha,
        "global_order": "overview_header_all_pages_all_raw_ranges_then_checklist",
        "completed_command_count": len(records),
        "completed_command_event_ids": [record["id"] for record in records],
        "source_coverage_receipt": source_receipt,
        "checklist_read": {
            "completed_event_id": final["id"],
            "completed_output_sha256": sha256_text(final["output"]),
            "completion_proof": completion,
        },
        "codex_0144_event_framing": event_framing,
        "additional_command_count": 0,
        "forbidden_tool_event_count": 0,
    }
    payload["coverage_receipt_sha256"] = canonical_sha256(payload)
    return payload
