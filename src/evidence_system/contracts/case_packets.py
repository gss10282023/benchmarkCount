"""Build local raw-case packets and Markdown case packets from official sources."""

from __future__ import annotations

import json
import shlex
import re
import shutil
import subprocess
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import ContractLifecycleError, LifecycleIssue, find_forbidden_inputs, normalize_domain
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml


CASE_PACKET_SCHEMA_VERSION = "contract_source_bundle.v2"


@dataclass(frozen=True)
class SelectedCaseUnit:
    domain: str
    case_unit_id: str
    task_id: str


@dataclass(frozen=True)
class BuiltCasePacket:
    domain: str
    case_unit_id: str
    task_id: str
    case_dir: str
    raw_case_dir: str
    raw_case_manifest_path: str
    case_packet_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "case_unit_id": self.case_unit_id,
            "task_id": self.task_id,
            "case_dir": self.case_dir,
            "raw_case_dir": self.raw_case_dir,
            "raw_case_manifest_path": self.raw_case_manifest_path,
            "case_packet_path": self.case_packet_path,
        }


@dataclass(frozen=True)
class RemoteMachine:
    host: str
    user: str
    port: int
    key_path: str

    @property
    def target(self) -> str:
        return f"{self.user}@{self.host}"


def load_selected_case_units(
    manifest_path: str | Path,
    *,
    limit: int | None = None,
    per_domain_limit: int | None = None,
    case_unit_ids: Iterable[str] | None = None,
) -> list[SelectedCaseUnit]:
    payload = load_json_or_yaml(manifest_path)
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError("experiment manifest must be a mapping")
    requested = {str(item) for item in case_unit_ids or []}
    selected: list[SelectedCaseUnit] = []
    per_domain_counts: dict[str, int] = defaultdict(int)
    for block in payload.get("domains", []):
        if not isinstance(block, Mapping):
            continue
        domain = normalize_domain(block.get("domain"))
        for case_unit in block.get("case_units", []):
            if not isinstance(case_unit, Mapping):
                continue
            case_unit_id = str(case_unit.get("case_unit_id") or "")
            task_id = str(case_unit.get("task_id") or "")
            if not case_unit_id or not task_id:
                continue
            if requested and case_unit_id not in requested:
                continue
            if per_domain_limit is not None and per_domain_counts[domain] >= per_domain_limit:
                continue
            selected.append(SelectedCaseUnit(domain=domain, case_unit_id=case_unit_id, task_id=task_id))
            per_domain_counts[domain] += 1
            if limit is not None and len(selected) >= limit:
                return selected
    if requested:
        missing = requested - {item.case_unit_id for item in selected}
        if missing:
            raise ContractLifecycleError(f"case units not found in manifest: {', '.join(sorted(missing))}")
    return selected


def build_case_packets(
    *,
    manifest_path: str | Path = "experiments/experiment_manifest.yaml",
    official_splits_path: str | Path = "experiments/official_splits",
    output_root: str | Path = "experiments/case_packets",
    source_mode: str = "local",
    infra_config_path: str | Path = "configs/infra.yaml",
    limit: int | None = None,
    per_domain_limit: int | None = None,
    case_unit_ids: Iterable[str] | None = None,
) -> list[BuiltCasePacket]:
    selected = load_selected_case_units(
        manifest_path,
        limit=limit,
        per_domain_limit=per_domain_limit,
        case_unit_ids=case_unit_ids,
    )
    sources = OfficialCaseSources(official_splits_path)
    built: list[BuiltCasePacket] = []
    output_base = resolve_repo_path(output_root)
    output_base.mkdir(parents=True, exist_ok=True)
    source_mode_normalized = str(source_mode or "local").strip().lower()
    if source_mode_normalized not in {"local", "remote"}:
        raise ContractLifecycleError("source_mode must be 'local' or 'remote'")
    remote = RemoteCaseSources(infra_config_path) if source_mode_normalized == "remote" else None
    for item in selected:
        built.append(
            _build_one_case_packet(
                item,
                output_base=output_base,
                sources=sources,
                source_mode=source_mode_normalized,
                remote=remote,
            )
        )
    return built


def build_case_packet_source_bundle(
    *,
    manifest_path: str | Path = "experiments/experiment_manifest.yaml",
    case_packets_root: str | Path = "experiments/case_packets",
    previous_source_bundle_path: str | Path = "experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json",
    output_path: str | Path = "experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json",
    allow_generated_contract_ids: bool = False,
) -> Path:
    selected = load_selected_case_units(manifest_path)
    previous_sources: list[Any] = []
    previous_resolved = resolve_repo_path(previous_source_bundle_path)
    if previous_resolved.exists():
        previous = load_json_or_yaml(previous_resolved)
        if not isinstance(previous, Mapping):
            raise ContractLifecycleError("previous source bundle must be a mapping")
        previous_sources = list(previous.get("sources") or [])
    contract_ids: dict[str, str] = {}
    for source in previous_sources:
        if not isinstance(source, Mapping):
            continue
        case_unit_id = str(source.get("case_unit_id") or "")
        contract_id = str(source.get("contract_id") or "")
        if case_unit_id and contract_id:
            contract_ids[case_unit_id] = contract_id
    sources_payload: list[dict[str, Any]] = []
    for item in selected:
        contract_id = contract_ids.get(item.case_unit_id)
        if not contract_id:
            if not allow_generated_contract_ids:
                raise ContractLifecycleError(f"missing legacy contract_id for case unit {item.case_unit_id}")
            contract_id = _generated_contract_id(item.domain, item.case_unit_id)
        case_dir = resolve_repo_path(case_packets_root) / item.domain / _safe_case_dir_name(item.case_unit_id)
        packet_path = case_dir / "case_packet.md"
        manifest_file = case_dir / "raw_case_manifest.json"
        if not packet_path.exists() or not manifest_file.exists():
            raise ContractLifecycleError(f"case packet files missing for {item.case_unit_id}: {case_dir}")
        sources_payload.append(
            {
                "contract_id": contract_id,
                "domain": item.domain,
                "case_unit_id": item.case_unit_id,
                "task_id": item.task_id,
                "draft_input": {
                    "case_packet_path": _repo_relative(packet_path),
                    "case_packet_sha256": sha256_file(packet_path),
                    "raw_case_manifest_path": _repo_relative(manifest_file),
                    "raw_case_manifest_sha256": sha256_file(manifest_file),
                },
            }
        )
    payload = {
        "schema_version": CASE_PACKET_SCHEMA_VERSION,
        "manifest_path": _repo_relative(resolve_repo_path(manifest_path)),
        "source_count": len(sources_payload),
        "sources": sources_payload,
    }
    resolved = resolve_repo_path(output_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


def load_case_packet_markdown(source: Mapping[str, Any]) -> str:
    draft_input = _draft_input(source)
    packet_path = resolve_repo_path(str(draft_input["case_packet_path"]))
    return packet_path.read_text(encoding="utf-8")


def load_raw_case_manifest(source: Mapping[str, Any]) -> dict[str, Any]:
    draft_input = _draft_input(source)
    manifest_path = resolve_repo_path(str(draft_input["raw_case_manifest_path"]))
    payload = load_json_or_yaml(manifest_path)
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError("raw_case_manifest.json must be a mapping")
    return dict(payload)


def validate_case_packet_source(source: Mapping[str, Any], base: str = "$") -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = find_forbidden_inputs(source, base)
    draft_input = source.get("draft_input")
    if not isinstance(draft_input, Mapping):
        return [LifecycleIssue(f"{base}.draft_input", "source bundle item requires draft_input mapping")]
    for field in ("case_packet_path", "case_packet_sha256", "raw_case_manifest_path", "raw_case_manifest_sha256"):
        value = draft_input.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(LifecycleIssue(f"{base}.draft_input.{field}", "required draft_input field is missing"))
    case_packet_path = draft_input.get("case_packet_path")
    raw_manifest_path = draft_input.get("raw_case_manifest_path")
    if isinstance(case_packet_path, str):
        issues.extend(_path_issues(case_packet_path, f"{base}.draft_input.case_packet_path"))
        packet_file = resolve_repo_path(case_packet_path)
        if not packet_file.exists():
            issues.append(LifecycleIssue(f"{base}.draft_input.case_packet_path", "case_packet.md file is missing"))
        elif draft_input.get("case_packet_sha256") != sha256_file(packet_file):
            issues.append(LifecycleIssue(f"{base}.draft_input.case_packet_sha256", "case_packet_sha256 does not match local file"))
    if isinstance(raw_manifest_path, str):
        issues.extend(_path_issues(raw_manifest_path, f"{base}.draft_input.raw_case_manifest_path"))
        manifest_file = resolve_repo_path(raw_manifest_path)
        if not manifest_file.exists():
            issues.append(LifecycleIssue(f"{base}.draft_input.raw_case_manifest_path", "raw_case_manifest.json file is missing"))
        elif draft_input.get("raw_case_manifest_sha256") != sha256_file(manifest_file):
            issues.append(
                LifecycleIssue(f"{base}.draft_input.raw_case_manifest_sha256", "raw_case_manifest_sha256 does not match local file")
            )
        else:
            manifest = load_json_or_yaml(manifest_file)
            if not isinstance(manifest, Mapping):
                issues.append(LifecycleIssue(f"{base}.draft_input.raw_case_manifest_path", "raw_case_manifest.json must be a mapping"))
            else:
                for field in (
                    "domain",
                    "case_unit_id",
                    "task_id",
                    "source_refs",
                    "copied_files",
                    "official_files",
                    "derived_files",
                    "packet_files",
                    "sha256_per_file",
                ):
                    if field not in manifest:
                        issues.append(LifecycleIssue(f"{base}.draft_input.raw_case_manifest_path.{field}", "raw_case_manifest field is missing"))
    return issues


def derive_source_context(source: Mapping[str, Any]) -> dict[str, Any]:
    manifest = load_raw_case_manifest(source)
    domain = normalize_domain(source.get("domain") or manifest.get("domain"))
    raw_case_dir = resolve_repo_path(str(source_path_from_manifest(source)))
    if domain == "agentdojo":
        return _agentdojo_context(raw_case_dir, manifest)
    if domain == "appworld":
        return _appworld_context(raw_case_dir, manifest)
    if domain == "miniwob":
        return _miniwob_context(raw_case_dir, manifest)
    if domain == "androidworld":
        return _androidworld_context(raw_case_dir, manifest)
    if domain == "webarena_verified":
        return _webarena_context(raw_case_dir, manifest)
    if domain == "workarena":
        return _workarena_context(raw_case_dir, manifest)
    if domain == "tau3_retail":
        return _tau3_context(raw_case_dir, manifest)
    raise ContractLifecycleError(f"unsupported case-packet domain: {domain}")


def source_path_from_manifest(source: Mapping[str, Any]) -> Path:
    manifest_path = resolve_repo_path(str(_draft_input(source)["raw_case_manifest_path"]))
    return manifest_path.parent / "raw_case"


class OfficialCaseSources:
    def __init__(self, official_splits_path: str | Path) -> None:
        self.root = resolve_repo_path(official_splits_path)
        self._agentdojo: dict[str, Mapping[str, Any]] | None = None
        self._appworld: dict[str, Mapping[str, Any]] | None = None
        self._miniwob: dict[str, Mapping[str, Any]] | None = None
        self._androidworld: dict[str, Mapping[str, Any]] | None = None
        self._webarena: dict[str, Mapping[str, Any]] | None = None
        self._workarena: dict[str, Mapping[str, Any]] | None = None
        self._tau3: dict[str, Mapping[str, Any]] | None = None
        self._tau3_policy: str | None = None

    def agentdojo_item(self, case_unit_id: str) -> Mapping[str, Any]:
        if self._agentdojo is None:
            payload = load_json_or_yaml(self.root / "agentdojo_selected_task_sources.json")
            if not isinstance(payload, Mapping):
                raise ContractLifecycleError("agentdojo_selected_task_sources.json must be a mapping")
            items = payload.get("items")
            if not isinstance(items, Sequence):
                raise ContractLifecycleError("agentdojo_selected_task_sources.json missing items")
            self._agentdojo = {
                str(item.get("case_unit_id")): item for item in items if isinstance(item, Mapping) and item.get("case_unit_id")
            }
        try:
            return self._agentdojo[case_unit_id]
        except KeyError as exc:
            raise ContractLifecycleError(f"missing AgentDojo official source for {case_unit_id}") from exc

    def appworld_item(self, task_id: str) -> Mapping[str, Any]:
        if self._appworld is None:
            payload = load_json_or_yaml(self.root / "appworld_selected_task_sources.json")
            if not isinstance(payload, Mapping):
                raise ContractLifecycleError("appworld_selected_task_sources.json must be a mapping")
            items = payload.get("items")
            if not isinstance(items, Sequence):
                raise ContractLifecycleError("appworld_selected_task_sources.json missing items")
            self._appworld = {
                str(item.get("task_id")): item for item in items if isinstance(item, Mapping) and item.get("task_id")
            }
        try:
            return self._appworld[task_id]
        except KeyError as exc:
            raise ContractLifecycleError(f"missing AppWorld official source for {task_id}") from exc

    def miniwob_item(self, task_id: str) -> Mapping[str, Any]:
        if self._miniwob is None:
            payload = load_json_or_yaml(self.root / "miniwob_selected_task_sources.json")
            if not isinstance(payload, Mapping):
                raise ContractLifecycleError("miniwob_selected_task_sources.json must be a mapping")
            items = payload.get("items")
            if not isinstance(items, Sequence):
                raise ContractLifecycleError("miniwob_selected_task_sources.json missing items")
            self._miniwob = {
                str(item.get("task_id")): item for item in items if isinstance(item, Mapping) and item.get("task_id")
            }
        try:
            return self._miniwob[task_id]
        except KeyError as exc:
            raise ContractLifecycleError(f"missing MiniWoB++ official source for {task_id}") from exc

    def androidworld_item(self, task_id: str) -> Mapping[str, Any]:
        if self._androidworld is None:
            payload = load_json_or_yaml(self.root / "androidworld_selected_task_sources.json")
            if not isinstance(payload, Mapping):
                raise ContractLifecycleError("androidworld_selected_task_sources.json must be a mapping")
            items = payload.get("items")
            if not isinstance(items, Sequence):
                raise ContractLifecycleError("androidworld_selected_task_sources.json missing items")
            self._androidworld = {
                str(item.get("task_id")): item for item in items if isinstance(item, Mapping) and item.get("task_id")
            }
        try:
            return self._androidworld[task_id]
        except KeyError as exc:
            raise ContractLifecycleError(f"missing AndroidWorld official source for {task_id}") from exc

    def webarena_item(self, task_id: str) -> Mapping[str, Any]:
        if self._webarena is None:
            payload = load_json_or_yaml(self.root / "webarena_verified_official_812.json")
            if not isinstance(payload, list):
                raise ContractLifecycleError("webarena_verified_official_812.json must be a list")
            self._webarena = {
                str(item.get("task_id")): item for item in payload if isinstance(item, Mapping) and item.get("task_id") is not None
            }
        try:
            return self._webarena[str(int(task_id))]
        except (KeyError, ValueError) as exc:
            raise ContractLifecycleError(f"missing WebArena official source for {task_id}") from exc

    def workarena_item(self, task_id: str) -> Mapping[str, Any]:
        if self._workarena is None:
            payload = load_json_or_yaml(self.root / "workarena_selected_task_sources.json")
            if not isinstance(payload, Mapping):
                raise ContractLifecycleError("workarena_selected_task_sources.json must be a mapping")
            items = payload.get("items")
            if not isinstance(items, Sequence):
                raise ContractLifecycleError("workarena_selected_task_sources.json missing items")
            self._workarena = {
                str(item.get("task_id")): item for item in items if isinstance(item, Mapping) and item.get("task_id")
            }
        try:
            return self._workarena[task_id]
        except KeyError as exc:
            raise ContractLifecycleError(f"missing WorkArena official source for {task_id}") from exc

    def tau3_item(self, task_id: str) -> Mapping[str, Any]:
        if self._tau3 is None:
            payload = load_json_or_yaml(self.root / "tau3_retail_tasks.json")
            if not isinstance(payload, list):
                raise ContractLifecycleError("tau3_retail_tasks.json must be a list")
            self._tau3 = {
                str(item.get("id")): item for item in payload if isinstance(item, Mapping) and item.get("id") is not None
            }
        try:
            return self._tau3[task_id]
        except KeyError as exc:
            raise ContractLifecycleError(f"missing tau3 retail official source for {task_id}") from exc

    def tau3_policy(self) -> str:
        if self._tau3_policy is None:
            self._tau3_policy = (self.root / "tau3_retail_policy.md").read_text(encoding="utf-8")
        return self._tau3_policy


class RemoteCaseSources:
    def __init__(self, infra_config_path: str | Path) -> None:
        payload = load_json_or_yaml(infra_config_path)
        if not isinstance(payload, Mapping):
            raise ContractLifecycleError("infra config must be a mapping")
        self._payload = payload
        self._cache: dict[str, bytes] = {}
        self._agentdojo_machine = self._machine_for_benchmark("AgentDojo")
        self._appworld_machine = self._machine_for_benchmark("AppWorld")
        self._miniwob_machine = self._machine_for_benchmark("MiniWoB++")
        self._workarena_machine = self._machine_for_benchmark("WorkArena")
        self._tau3_machine = self._machine_for_benchmark("τ³-bench retail")

    @property
    def agentdojo_machine(self) -> RemoteMachine:
        return self._agentdojo_machine

    @property
    def appworld_machine(self) -> RemoteMachine:
        return self._appworld_machine

    @property
    def miniwob_machine(self) -> RemoteMachine:
        return self._miniwob_machine

    @property
    def workarena_machine(self) -> RemoteMachine:
        return self._workarena_machine

    @property
    def tau3_machine(self) -> RemoteMachine:
        return self._tau3_machine

    def _machine_for_benchmark(self, benchmark_name: str) -> RemoteMachine:
        for machine in self._payload.get("machines") or []:
            if not isinstance(machine, Mapping) or machine.get("enabled") is False:
                continue
            benchmarks = machine.get("benchmarks") or {}
            if not isinstance(benchmarks, Mapping) or benchmark_name not in benchmarks:
                continue
            ssh = machine.get("ssh") or {}
            if not isinstance(ssh, Mapping):
                break
            host = str(ssh.get("host") or "").strip()
            user = str(ssh.get("user") or "").strip()
            key_path = str(ssh.get("key_path") or "").strip()
            if not host or not user or not key_path:
                break
            return RemoteMachine(
                host=host,
                user=user,
                port=int(ssh.get("port") or 22),
                key_path=key_path,
            )
        raise ContractLifecycleError(f"unable to resolve enabled SSH machine for benchmark {benchmark_name}")

    def run(self, machine: RemoteMachine, command: str) -> str:
        argv = [
            "ssh",
            "-i",
            machine.key_path,
            "-p",
            str(machine.port),
            "-o",
            "StrictHostKeyChecking=no",
            machine.target,
            f"bash -lc {shlex.quote('set -euo pipefail\n' + command)}",
        ]
        completed = subprocess.run(argv, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise ContractLifecycleError(
                f"remote command failed on {machine.target}:\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            )
        return completed.stdout

    def copy_file(self, machine: RemoteMachine, remote_path: str, local_path: Path) -> None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        cache_key = f"{machine.target}:{remote_path}"
        data = self._cache.get(cache_key)
        if data is None:
            argv = [
                "scp",
                "-q",
                "-i",
                machine.key_path,
                "-P",
                str(machine.port),
                f"{machine.target}:{remote_path}",
                str(local_path),
            ]
            completed = subprocess.run(argv, text=True, capture_output=True, check=False)
            if completed.returncode != 0:
                raise ContractLifecycleError(
                    f"scp failed for {remote_path} from {machine.target}:\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
                )
            data = local_path.read_bytes()
            self._cache[cache_key] = data
            return
        local_path.write_bytes(data)

    def copy_directory(self, machine: RemoteMachine, remote_dir: str, local_dir: Path) -> None:
        local_dir.mkdir(parents=True, exist_ok=True)
        argv = [
            "scp",
            "-q",
            "-i",
            machine.key_path,
            "-P",
            str(machine.port),
            "-r",
            f"{machine.target}:{remote_dir.rstrip('/')}/.",
            str(local_dir),
        ]
        completed = subprocess.run(argv, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise ContractLifecycleError(
                f"scp -r failed for {remote_dir} from {machine.target}:\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            )

    def remote_directory_inventory(self, machine: RemoteMachine, remote_dir: str) -> dict[str, str]:
        script = f"""
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
root = Path({remote_dir!r})
payload = {{}}
for path in sorted(p for p in root.rglob('*') if p.is_file()):
    if path.suffix == '.pyc' or '__pycache__' in path.parts:
        continue
    payload[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps(payload, sort_keys=True))
PY
"""
        text = self.run(machine, script)
        payload = json.loads(text or "{}")
        if not isinstance(payload, dict):
            raise ContractLifecycleError(f"remote directory inventory for {remote_dir} must be a mapping")
        return {str(key): str(value) for key, value in payload.items()}

    def remote_file_hashes(self, machine: RemoteMachine, remote_paths: Sequence[str]) -> dict[str, str]:
        listing = json.dumps(list(remote_paths))
        script = f"""
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
paths = json.loads({listing!r})
payload = {{}}
for raw in paths:
    path = Path(raw)
    payload[raw] = hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps(payload, sort_keys=True))
PY
"""
        text = self.run(machine, script)
        payload = json.loads(text or "{}")
        if not isinstance(payload, dict):
            raise ContractLifecycleError("remote file hash payload must be a mapping")
        return {str(key): str(value) for key, value in payload.items()}

    def agentdojo_case_metadata(self, case_unit_id: str) -> dict[str, Any]:
        benchmark_version, suite_name, user_task_id, injection_task_id = _parse_agentdojo_case_unit_id(case_unit_id)
        payload = {
            "benchmark_version": benchmark_version,
            "suite_name": suite_name,
            "user_task_id": user_task_id,
            "injection_task_id": injection_task_id,
        }
        script = f"""
<AGENTDOJO_INSTALL_ROOT>/.venv/bin/python - <<'PY'
import ast
import importlib
import inspect
import json
from pathlib import Path
from agentdojo.task_suite import get_suites

payload = json.loads({json.dumps(json.dumps(payload))})
suite = get_suites(payload["benchmark_version"])[payload["suite_name"]]
user_task = suite.get_user_task_by_id(payload["user_task_id"])
injection_task = suite.get_injection_task_by_id(payload["injection_task_id"])
user_path = Path(inspect.getfile(user_task.__class__)).resolve()
injection_path = Path(inspect.getfile(injection_task.__class__)).resolve()
task_suite_path = user_path.parent / "task_suite.py"
module = ast.parse(user_path.read_text(encoding="utf-8"))
for node in module.body:
    if not isinstance(node, ast.ImportFrom):
        continue
    imported = {{alias.name for alias in node.names}}
    if "task_suite" not in imported or not node.module:
        continue
    task_suite_path = Path(inspect.getfile(importlib.import_module(node.module))).resolve()
    break
tools_dir = task_suite_path.parent.parent / "tools"
package_root = user_path.parents[4]
if suite.data_path is None:
    data_path = package_root / "agentdojo" / "data" / "suites" / suite.name
else:
    data_path = Path(suite.data_path).resolve()
result = {{
    "user_source_file": str(user_path),
    "injection_source_file": str(injection_path),
    "task_suite_file": str(task_suite_path),
    "package_root": str(package_root),
    "data_files": [
        str(path.resolve())
        for path in sorted(p for p in data_path.rglob("*") if p.is_file())
    ],
    "tool_files": [
        str(path.resolve())
        for path in sorted(p for p in tools_dir.glob("*.py"))
    ],
}}
print(json.dumps(result, sort_keys=True))
PY
"""
        text = self.run(self.agentdojo_machine, script)
        result = json.loads(text or "{}")
        if not isinstance(result, Mapping):
            raise ContractLifecycleError(f"remote AgentDojo metadata for {case_unit_id} must be a mapping")
        return dict(result)


def _build_one_case_packet(
    item: SelectedCaseUnit,
    *,
    output_base: Path,
    sources: OfficialCaseSources,
    source_mode: str,
    remote: RemoteCaseSources | None,
) -> BuiltCasePacket:
    case_dir = output_base / item.domain / _safe_case_dir_name(item.case_unit_id)
    if case_dir.exists():
        shutil.rmtree(case_dir)
    raw_case_dir = case_dir / "raw_case"
    raw_case_dir.mkdir(parents=True, exist_ok=True)
    file_sources: dict[str, str] = {}
    source_refs: list[str] = []
    official_files: list[str] = []
    derived_files: list[str] = []
    packet_files: list[str] = []

    if source_mode == "local":
        if item.domain == "agentdojo":
            payload = dict(sources.agentdojo_item(item.case_unit_id))
            source_ref = str(payload.get("source_ref") or "agentdojo_selected_task_sources.json")
            target = raw_case_dir / "selected_task_source.json"
            _write_json_like(target, payload)
            file_sources["selected_task_source.json"] = source_ref
            source_refs = [source_ref]
            official_files = ["selected_task_source.json"]
            packet_files = ["selected_task_source.json"]
        elif item.domain == "appworld":
            payload = dict(sources.appworld_item(item.task_id))
            files = payload.get("files")
            if not isinstance(files, Mapping):
                raise ContractLifecycleError(f"AppWorld source files missing for {item.task_id}")
            source_refs = [str(payload.get("source_ref") or ""), str(payload.get("task_dir") or "")]
            for relative, descriptor in sorted(files.items()):
                if not isinstance(descriptor, Mapping):
                    continue
                target = raw_case_dir / str(relative)
                content = descriptor.get("content")
                _write_source_file(target, content)
                rel = str(target.relative_to(raw_case_dir))
                file_sources[rel] = str(payload.get("task_dir") or payload.get("source_ref") or "")
                official_files.append(rel)
            packet_files = list(official_files)
        elif item.domain == "miniwob":
            payload = dict(sources.miniwob_item(item.task_id))
            official_files, derived_files, packet_files, source_refs = _materialize_local_file_list_case(
                raw_case_dir,
                payload=payload,
                file_sources=file_sources,
                source_ref_default="miniwob_selected_task_sources.json",
            )
        elif item.domain == "androidworld":
            payload = dict(sources.androidworld_item(item.task_id))
            official_files, derived_files, packet_files, source_refs = _materialize_local_file_list_case(
                raw_case_dir,
                payload=payload,
                file_sources=file_sources,
                source_ref_default="androidworld_selected_task_sources.json",
            )
        elif item.domain == "webarena_verified":
            payload = dict(sources.webarena_item(item.task_id))
            source_ref = f"experiments/official_splits/webarena_verified_official_812.json#task_id={item.task_id}"
            _write_json_like(raw_case_dir / "task.json", payload)
            file_sources["task.json"] = source_ref
            source_refs = [source_ref]
            official_files = ["task.json"]
            packet_files = ["task.json"]
        elif item.domain == "tau3_retail":
            payload = dict(sources.tau3_item(item.task_id))
            policy_text = sources.tau3_policy()
            source_refs = [
                f"experiments/official_splits/tau3_retail_tasks.json#id={item.task_id}",
                "experiments/official_splits/tau3_retail_policy.md",
            ]
            _write_json_like(raw_case_dir / "task.json", payload)
            (raw_case_dir / "policy.md").write_text(policy_text, encoding="utf-8")
            file_sources["task.json"] = source_refs[0]
            file_sources["policy.md"] = source_refs[1]
            official_files = ["task.json", "policy.md"]
            packet_files = list(official_files)
        elif item.domain == "workarena":
            payload = dict(sources.workarena_item(item.task_id))
            official_files, derived_files, packet_files, source_refs = _materialize_local_file_list_case(
                raw_case_dir,
                payload=payload,
                file_sources=file_sources,
                source_ref_default="workarena_selected_task_sources.json",
            )
        else:
            raise ContractLifecycleError(f"unsupported case-packet domain: {item.domain}")
    else:
        if remote is None:
            raise ContractLifecycleError("remote source mode requires remote case sources")
        if item.domain == "agentdojo":
            payload = dict(sources.agentdojo_item(item.case_unit_id))
            metadata = remote.agentdojo_case_metadata(item.case_unit_id)
            package_root = str(metadata.get("package_root") or "").strip()
            if not package_root:
                raise ContractLifecycleError(f"AgentDojo metadata missing package_root for {item.case_unit_id}")
            official_root = raw_case_dir / "official"
            copied: list[str] = []
            remote_paths = [
                str(metadata.get("user_source_file") or ""),
                str(metadata.get("injection_source_file") or ""),
                str(metadata.get("task_suite_file") or ""),
                *[str(value) for value in metadata.get("tool_files") or []],
                *[str(value) for value in metadata.get("data_files") or []],
            ]
            remote_paths = [path_text.strip() for path_text in remote_paths if str(path_text).strip()]
            for remote_path in remote_paths:
                path_text = remote_path.strip()
                rel = _relative_remote_path(path_text, package_root)
                target = official_root / rel
                remote.copy_file(remote.agentdojo_machine, path_text, target)
                rel_in_case = str(target.relative_to(raw_case_dir))
                file_sources[rel_in_case] = path_text
                copied.append(rel_in_case)
            expected_inventory = {
                f"official/{_relative_remote_path(path_text, package_root)}": remote_hash
                for path_text, remote_hash in remote.remote_file_hashes(remote.agentdojo_machine, remote_paths).items()
            }
            actual_inventory = {f"official/{key}": value for key, value in _local_inventory(official_root).items()}
            _ensure_inventory_matches(f"AgentDojo {item.case_unit_id}", expected_inventory, actual_inventory)
            helper = raw_case_dir / "derived" / "selected_task_source.json"
            _write_json_like(helper, payload)
            helper_rel = str(helper.relative_to(raw_case_dir))
            file_sources[helper_rel] = str(payload.get("source_ref") or "agentdojo_selected_task_sources.json")
            source_refs = sorted({str(value) for value in file_sources.values() if value})
            official_files = sorted(set(copied))
            derived_files = [helper_rel]
            packet_files = list(official_files)
        elif item.domain == "appworld":
            payload = dict(sources.appworld_item(item.task_id))
            remote_dir = str(payload.get("task_dir") or "").strip()
            if not remote_dir:
                raise ContractLifecycleError(f"AppWorld task_dir missing for {item.task_id}")
            official_root = raw_case_dir / "official"
            remote.copy_directory(remote.appworld_machine, remote_dir, official_root)
            _prune_generated_files(official_root)
            inventory = _local_inventory(official_root)
            for rel in sorted(inventory):
                rel_in_case = f"official/{rel}"
                file_sources[rel_in_case] = remote_dir
                official_files.append(rel_in_case)
            expected_inventory = {
                f"official/{rel}": value for rel, value in remote.remote_directory_inventory(remote.appworld_machine, remote_dir).items()
            }
            actual_inventory = {f"official/{rel}": value for rel, value in inventory.items()}
            _ensure_inventory_matches(f"AppWorld {item.case_unit_id}", expected_inventory, actual_inventory)
            source_refs = [str(payload.get("source_ref") or ""), remote_dir]
            packet_files = list(sorted(official_files))
        elif item.domain == "miniwob":
            payload = dict(sources.miniwob_item(item.task_id))
            official_files, derived_files, packet_files, source_refs = _materialize_remote_file_list_case(
                raw_case_dir,
                payload=payload,
                remote=remote,
                machine=remote.miniwob_machine,
                file_sources=file_sources,
                source_ref_default="miniwob_selected_task_sources.json",
                label=f"MiniWoB++ {item.case_unit_id}",
            )
        elif item.domain == "androidworld":
            payload = dict(sources.androidworld_item(item.task_id))
            official_files, derived_files, packet_files, source_refs = _materialize_local_file_list_case(
                raw_case_dir,
                payload=payload,
                file_sources=file_sources,
                source_ref_default="androidworld_selected_task_sources.json",
            )
        elif item.domain == "webarena_verified":
            payload = dict(sources.webarena_item(item.task_id))
            official_root = raw_case_dir / "official"
            official_root.mkdir(parents=True, exist_ok=True)
            source_file = resolve_repo_path("experiments/official_splits/webarena_verified_official_812.json")
            target = official_root / "webarena-verified.json"
            shutil.copy2(source_file, target)
            official_rel = str(target.relative_to(raw_case_dir))
            file_sources[official_rel] = str(source_file)
            derived = raw_case_dir / "derived" / "task.json"
            _write_json_like(derived, payload)
            derived_rel = str(derived.relative_to(raw_case_dir))
            file_sources[derived_rel] = f"{source_file}#task_id={item.task_id}"
            source_refs = [str(source_file), file_sources[derived_rel]]
            official_files = [official_rel]
            derived_files = [derived_rel]
            packet_files = [derived_rel]
            _ensure_inventory_matches(
                f"WebArena {item.case_unit_id}",
                {official_rel: sha256_file(source_file)},
                {official_rel: sha256_file(target)},
            )
        elif item.domain == "tau3_retail":
            payload = dict(sources.tau3_item(item.task_id))
            official_root = raw_case_dir / "official"
            official_root.mkdir(parents=True, exist_ok=True)
            local_officials = {
                "tasks.json": resolve_repo_path("experiments/official_splits/tau3_retail_tasks.json"),
                "policy.md": resolve_repo_path("experiments/official_splits/tau3_retail_policy.md"),
                "split_tasks.json": resolve_repo_path("experiments/official_splits/tau3_retail_split_tasks.json"),
            }
            for name, source_file in local_officials.items():
                target = official_root / name
                shutil.copy2(source_file, target)
                rel = str(target.relative_to(raw_case_dir))
                file_sources[rel] = str(source_file)
                official_files.append(rel)
            db_remote = "<TAU2_BENCH_INSTALL_ROOT>/data/tau2/domains/retail/db.json"
            db_target = official_root / "db.json"
            remote.copy_file(remote.tau3_machine, db_remote, db_target)
            db_rel = str(db_target.relative_to(raw_case_dir))
            file_sources[db_rel] = db_remote
            official_files.append(db_rel)
            expected_inventory = {
                "official/tasks.json": sha256_file(local_officials["tasks.json"]),
                "official/policy.md": sha256_file(local_officials["policy.md"]),
                "official/split_tasks.json": sha256_file(local_officials["split_tasks.json"]),
                "official/db.json": next(iter(remote.remote_file_hashes(remote.tau3_machine, [db_remote]).values())),
            }
            actual_inventory = {f"official/{rel}": value for rel, value in _local_inventory(official_root).items()}
            _ensure_inventory_matches(f"tau3 retail {item.case_unit_id}", expected_inventory, actual_inventory)
            derived = raw_case_dir / "derived" / "task.json"
            _write_json_like(derived, payload)
            derived_rel = str(derived.relative_to(raw_case_dir))
            file_sources[derived_rel] = f"{local_officials['tasks.json']}#id={item.task_id}"
            source_refs = [str(local_officials["tasks.json"]), str(local_officials["policy.md"]), str(local_officials["split_tasks.json"]), db_remote]
            derived_files = [derived_rel]
            packet_files = [derived_rel, "official/policy.md", "official/split_tasks.json"]
        elif item.domain == "workarena":
            payload = dict(sources.workarena_item(item.task_id))
            official_files, derived_files, packet_files, source_refs = _materialize_remote_file_list_case(
                raw_case_dir,
                payload=payload,
                remote=remote,
                machine=remote.workarena_machine,
                file_sources=file_sources,
                source_ref_default="workarena_selected_task_sources.json",
                label=f"WorkArena {item.case_unit_id}",
            )
        else:
            raise ContractLifecycleError(f"unsupported case-packet domain: {item.domain}")

    raw_case_manifest = _raw_case_manifest(
        domain=item.domain,
        case_unit_id=item.case_unit_id,
        task_id=item.task_id,
        raw_case_dir=raw_case_dir,
        source_refs=[ref for ref in source_refs if ref],
        file_sources=file_sources,
        official_files=official_files,
        derived_files=derived_files,
        packet_files=packet_files,
    )
    raw_case_manifest_path = case_dir / "raw_case_manifest.json"
    raw_case_manifest_path.write_text(json.dumps(raw_case_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    case_packet_path = case_dir / "case_packet.md"
    case_packet_path.write_text(
        render_case_packet(
            domain=item.domain,
            case_unit_id=item.case_unit_id,
            task_id=item.task_id,
            raw_case_dir=raw_case_dir,
            raw_case_manifest=raw_case_manifest,
        ),
        encoding="utf-8",
    )
    return BuiltCasePacket(
        domain=item.domain,
        case_unit_id=item.case_unit_id,
        task_id=item.task_id,
        case_dir=_repo_relative(case_dir),
        raw_case_dir=_repo_relative(raw_case_dir),
        raw_case_manifest_path=_repo_relative(raw_case_manifest_path),
        case_packet_path=_repo_relative(case_packet_path),
    )


def _draft_input(source: Mapping[str, Any]) -> Mapping[str, Any]:
    draft_input = source.get("draft_input")
    if not isinstance(draft_input, Mapping):
        raise ContractLifecycleError("source item has no draft_input mapping")
    return draft_input


def render_case_packet(
    *,
    domain: str,
    case_unit_id: str,
    task_id: str,
    raw_case_dir: Path,
    raw_case_manifest: Mapping[str, Any],
) -> str:
    lines = [
        "# Case Packet",
        "",
        "## Case Metadata",
        "",
        f"- domain: `{domain}`",
        f"- case_unit_id: `{case_unit_id}`",
        f"- task_id: `{task_id}`",
        "",
        "## Source Inventory",
        "",
    ]
    packet_files = [str(item) for item in raw_case_manifest.get("packet_files") or []]
    if packet_files:
        files = [raw_case_dir / rel for rel in packet_files]
    else:
        files = sorted(path for path in raw_case_dir.rglob("*") if path.is_file())
    for path in files:
        lines.append(f"- `{path.relative_to(raw_case_dir)}`")
    lines.extend(["", "## Packet Source Files", ""])
    for path in files:
        relpath = path.relative_to(raw_case_dir)
        source_ref = str((raw_case_manifest.get("file_sources") or {}).get(str(relpath)) or "")
        lines.append(f"### `{relpath}`")
        lines.append("")
        if source_ref:
            lines.append(f"Source ref: `{source_ref}`")
            lines.append("")
        fence = _markdown_fence(path)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = f"[binary file omitted from packet; sha256={sha256_file(path)}]"
            fence = "text"
        lines.append(f"```{fence}")
        lines.append(content.rstrip("\n"))
        lines.append("```")
        lines.append("")
    lines.extend(
        [
            "## Raw Source Provenance",
            "",
            "```json",
            json.dumps(raw_case_manifest, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _raw_case_manifest(
    *,
    domain: str,
    case_unit_id: str,
    task_id: str,
    raw_case_dir: Path,
    source_refs: list[str],
    file_sources: Mapping[str, str],
    official_files: Sequence[str],
    derived_files: Sequence[str],
    packet_files: Sequence[str],
) -> dict[str, Any]:
    files = sorted(path for path in raw_case_dir.rglob("*") if path.is_file())
    copied_files = [str(path.relative_to(raw_case_dir)) for path in files]
    sha256_per_file = {str(path.relative_to(raw_case_dir)): sha256_file(path) for path in files}
    return {
        "domain": domain,
        "case_unit_id": case_unit_id,
        "task_id": task_id,
        "source_refs": source_refs,
        "copied_files": copied_files,
        "official_files": sorted(str(item) for item in official_files),
        "derived_files": sorted(str(item) for item in derived_files),
        "packet_files": [str(item) for item in packet_files],
        "sha256_per_file": sha256_per_file,
        "file_sources": {str(key): str(value) for key, value in sorted(file_sources.items())},
    }


def _materialize_local_file_list_case(
    raw_case_dir: Path,
    *,
    payload: Mapping[str, Any],
    file_sources: dict[str, str],
    source_ref_default: str,
) -> tuple[list[str], list[str], list[str], list[str]]:
    official_root = raw_case_dir / "official"
    copied: list[str] = []
    expected_inventory: dict[str, str] = {}
    for descriptor in list(payload.get("official_files") or []):
        if not isinstance(descriptor, Mapping):
            continue
        source_path = str(descriptor.get("source_path") or "").strip()
        archive_path = str(descriptor.get("archive_path") or "").strip()
        if not source_path or not archive_path:
            continue
        source_file = Path(source_path)
        if not source_file.exists():
            raise ContractLifecycleError(f"local source file missing for case packet build: {source_path}")
        target = raw_case_dir / archive_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
        rel = str(target.relative_to(raw_case_dir))
        file_sources[rel] = source_path
        copied.append(rel)
        expected_inventory[rel] = sha256_file(source_file)
    helper = raw_case_dir / "derived" / "selected_task_source.json"
    _write_json_like(helper, payload)
    helper_rel = str(helper.relative_to(raw_case_dir))
    file_sources[helper_rel] = str(payload.get("source_ref") or source_ref_default)
    actual_inventory = {rel: sha256_file(raw_case_dir / rel) for rel in copied}
    if expected_inventory:
        _ensure_inventory_matches(str(payload.get("task_id") or payload.get("case_unit_id") or "case"), expected_inventory, actual_inventory)
    packet_files = [str(item) for item in list(payload.get("packet_files") or [])] or sorted(copied)
    return sorted(copied), [helper_rel], packet_files, sorted({str(value) for value in file_sources.values() if value})


def _materialize_remote_file_list_case(
    raw_case_dir: Path,
    *,
    payload: Mapping[str, Any],
    remote: RemoteCaseSources,
    machine: RemoteMachine,
    file_sources: dict[str, str],
    source_ref_default: str,
    label: str,
) -> tuple[list[str], list[str], list[str], list[str]]:
    copied: list[str] = []
    remote_paths: list[str] = []
    expected_inventory: dict[str, str] = {}
    archive_lookup: dict[str, str] = {}
    for descriptor in list(payload.get("official_files") or []):
        if not isinstance(descriptor, Mapping):
            continue
        source_path = str(descriptor.get("source_path") or "").strip()
        archive_path = str(descriptor.get("archive_path") or "").strip()
        expected_hash = str(descriptor.get("sha256") or "").strip()
        if not source_path or not archive_path:
            continue
        remote_paths.append(source_path)
        archive_lookup[source_path] = archive_path
        if expected_hash:
            expected_inventory[archive_path] = expected_hash
    for remote_path in remote_paths:
        archive_path = archive_lookup[remote_path]
        target = raw_case_dir / archive_path
        remote.copy_file(machine, remote_path, target)
        rel = str(target.relative_to(raw_case_dir))
        file_sources[rel] = remote_path
        copied.append(rel)
    helper = raw_case_dir / "derived" / "selected_task_source.json"
    _write_json_like(helper, payload)
    helper_rel = str(helper.relative_to(raw_case_dir))
    file_sources[helper_rel] = str(payload.get("source_ref") or source_ref_default)
    actual_inventory = {rel: sha256_file(raw_case_dir / rel) for rel in copied}
    if expected_inventory:
        _ensure_inventory_matches(label, expected_inventory, actual_inventory)
    packet_files = [str(item) for item in list(payload.get("packet_files") or [])] or sorted(copied)
    return sorted(copied), [helper_rel], packet_files, sorted({str(value) for value in file_sources.values() if value})


def _path_issues(value: str, base: str) -> list[LifecycleIssue]:
    text = value.strip()
    if not text:
        return []
    if Path(text).is_absolute():
        return [LifecycleIssue(base, "source bundle must use repo-relative paths, not local absolute paths")]
    return []


def _write_source_file(path: Path, content: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
        return
    path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_json_like(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _local_inventory(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): sha256_file(path) for path in sorted(p for p in root.rglob("*") if p.is_file())}


def _prune_generated_files(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file() and path.suffix == ".pyc":
            path.unlink()
        elif path.is_dir() and path.name == "__pycache__":
            shutil.rmtree(path)


def _relative_remote_path(remote_path: str, root_path: str) -> str:
    try:
        return str(Path(remote_path).resolve().relative_to(Path(root_path).resolve()))
    except ValueError as exc:
        raise ContractLifecycleError(f"remote path {remote_path} is not under expected root {root_path}") from exc


def _ensure_inventory_matches(label: str, expected: Mapping[str, str], actual: Mapping[str, str]) -> None:
    expected_keys = set(expected)
    actual_keys = set(actual)
    if expected_keys != actual_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        problems: list[str] = []
        if missing:
            problems.append(f"missing={missing[:10]}")
        if extra:
            problems.append(f"extra={extra[:10]}")
        raise ContractLifecycleError(f"{label} file inventory mismatch: {'; '.join(problems)}")
    mismatched = sorted(key for key in expected_keys if str(expected[key]) != str(actual[key]))
    if mismatched:
        sample = mismatched[:10]
        raise ContractLifecycleError(f"{label} file hash mismatch for {sample}")


def _repo_relative(path: str | Path) -> str:
    resolved = resolve_repo_path(path)
    try:
        return str(resolved.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(resolved)


def _safe_case_dir_name(case_unit_id: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", case_unit_id).strip("_")
    return text or "case"


def _generated_contract_id(domain: str, case_unit_id: str) -> str:
    return f"ec_{normalize_domain(domain)}_{_safe_case_dir_name(case_unit_id)}_contract_v1_0_0"


def _markdown_fence(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".json": "json",
        ".md": "markdown",
        ".py": "python",
        ".txt": "text",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix, "text")


def _parse_agentdojo_case_unit_id(case_unit_id: str) -> tuple[str, str, str, str]:
    parts = case_unit_id.split(":")
    if len(parts) != 4:
        raise ContractLifecycleError(f"invalid AgentDojo case_unit_id: {case_unit_id}")
    benchmark_version, suite_name, user_task_id, injection_task_id = parts
    if not benchmark_version or not suite_name or not user_task_id or not injection_task_id:
        raise ContractLifecycleError(f"invalid AgentDojo case_unit_id: {case_unit_id}")
    return benchmark_version, suite_name, user_task_id, injection_task_id


def _agentdojo_context(raw_case_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    helper = raw_case_dir / "derived" / "selected_task_source.json"
    if not helper.exists():
        helper = raw_case_dir / "selected_task_source.json"
    payload = json.loads(helper.read_text(encoding="utf-8"))
    return {
        "task_text": {
            "benchmark": "AgentDojo",
            "benchmark_version": payload.get("benchmark_version"),
            "suite": payload.get("suite"),
            "user_task": {
                "id": payload.get("user_task", {}).get("id"),
                "prompt": payload.get("user_task", {}).get("prompt"),
            },
            "injection_task": {
                "id": payload.get("injection_task", {}).get("id"),
                "goal": payload.get("injection_task", {}).get("goal"),
            },
            "paired_arms": [
                "benign user task without injection",
                "same user task with selected injection task",
            ],
        },
        "official_policy": "No separate policy document is provided in the AgentDojo suite source; the task classes and suite tools are the official task/evaluator source for this case unit.",
        "evaluator_code": {
            "user_task_class_source": payload.get("user_task", {}).get("class_source"),
            "injection_task_class_source": payload.get("injection_task", {}).get("class_source"),
        },
        "evaluator_description": {
            "semantics": payload.get("evaluator_semantics"),
            "utility_ground_truth_output": payload.get("user_task", {}).get("ground_truth_output"),
            "security_ground_truth_output": payload.get("injection_task", {}).get("ground_truth_output"),
        },
        "schema": {
            "case_unit_schema": {
                "suite": payload.get("suite"),
                "user_task_id": "string",
                "injection_task_id": "string",
                "arms": ["benign", "injected"],
            },
            "suite_tools": payload.get("suite_tools") or [],
        },
        "trace_schema": {
            "episodes_per_record": 2,
            "benign_arm": ["messages", "tool calls", "workspace state"],
            "injected_arm": ["messages", "tool calls", "workspace state", "injection placement"],
        },
        "available_post_run_artifact_types": [
            "benign and injected arm traces",
            "observations",
            "actions",
            "tool calls",
            "files",
            "messages",
            "post-run artifacts",
            "native evaluator inputs",
        ],
        "contract_template": {"claim_scope": "native_aligned"},
        "native_sources": [
            {
                "source_ref": payload.get("source_ref"),
                "source_sha256": payload.get("source_sha256"),
            }
        ],
        "raw_case_manifest": dict(manifest),
    }


def _appworld_context(raw_case_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    official_root = raw_case_dir / "official" if (raw_case_dir / "official").exists() else raw_case_dir
    specs = json.loads((official_root / "specs.json").read_text(encoding="utf-8"))
    evaluation_code = (official_root / "ground_truth" / "evaluation.py").read_text(encoding="utf-8")
    public_data = json.loads((official_root / "ground_truth" / "public_data.json").read_text(encoding="utf-8"))
    private_data = json.loads((official_root / "ground_truth" / "private_data.json").read_text(encoding="utf-8"))
    test_data = json.loads((official_root / "ground_truth" / "test_data.json").read_text(encoding="utf-8"))
    metadata = json.loads((official_root / "ground_truth" / "metadata.json").read_text(encoding="utf-8"))
    return {
        "task_text": {
            "benchmark": "AppWorld",
            "instruction": specs.get("instruction"),
            "supervisor": specs.get("supervisor"),
            "datetime": specs.get("datetime"),
        },
        "official_policy": "No separate policy document is provided in AppWorld; the official task directory files and evaluator code are the official task/evaluator source for this case unit.",
        "evaluator_code": evaluation_code,
        "evaluator_description": {
            "test_data": test_data,
            "public_data": public_data,
            "private_data": private_data,
            "metadata": metadata,
        },
        "schema": {
            "task_directory": str(official_root),
            "files": sorted(str(path.relative_to(official_root)) for path in official_root.rglob("*") if path.is_file()),
        },
        "trace_schema": {
            "execution_mode": "single-run task directory evaluation",
            "available_ground_truth_files": [
                "ground_truth/evaluation.py",
                "ground_truth/public_data.json",
                "ground_truth/private_data.json",
                "ground_truth/test_data.json",
            ],
        },
        "available_post_run_artifact_types": [
            "native evaluator output",
            "native evaluator input",
            "database snapshot",
            "api log",
            "file",
            "structured output",
        ],
        "contract_template": {"claim_scope": "native_aligned"},
        "native_sources": [{"source_ref": ref} for ref in list(manifest.get("source_refs") or [])],
        "raw_case_manifest": dict(manifest),
    }


def _miniwob_context(raw_case_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    helper = raw_case_dir / "derived" / "selected_task_source.json"
    payload = json.loads(helper.read_text(encoding="utf-8"))
    return {
        "task_text": {
            "benchmark": "MiniWoB++",
            "task_id": payload.get("task_id"),
            "subdomain": payload.get("subdomain"),
            "runtime_goal_source": "observation.goal",
            "runtime_goal_note": "Read the exact task instruction from observation.goal at reset; MiniWoB++ episodes can vary by seed.",
            "static_title": payload.get("html_title"),
            "static_query_text": payload.get("static_query_text"),
        },
        "official_policy": "No separate policy document is provided in MiniWoB++; the official task class source, base validator, task HTML, and directly referenced frontend assets define the task and env.unwrapped.task.validate(page, chat_messages) semantics.",
        "evaluator_description": {
            "validator": "env.unwrapped.task.validate(page, chat_messages)",
            "task_class": payload.get("class_name"),
            "task_module": payload.get("module"),
            "base_class": payload.get("base_class_name"),
            "nondeterministic": payload.get("nondeterministic"),
        },
        "schema": {
            "subdomain": payload.get("subdomain"),
            "html_asset_files": payload.get("html_asset_files") or [],
        },
        "trace_schema": {
            "episodes_per_record": 1,
            "artifacts": [
                "browser state",
                "task trajectory",
                "validator inputs",
                "validator outputs",
                "structured final output",
            ],
        },
        "available_post_run_artifact_types": [
            "browser_artifact",
            "post_state",
            "trace",
            "native_evaluator_input",
            "native_evaluator_output",
            "structured_output",
            "file",
        ],
        "contract_template": {"claim_scope": "native_aligned"},
        "native_sources": [
            {
                "source_ref": payload.get("source_ref"),
                "source_sha256": payload.get("source_sha256"),
            }
        ],
        "raw_case_manifest": dict(manifest),
    }


def _androidworld_context(raw_case_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    helper = raw_case_dir / "derived" / "selected_task_source.json"
    payload = json.loads(helper.read_text(encoding="utf-8"))
    return {
        "task_text": {
            "benchmark": "AndroidWorld",
            "task_name": payload.get("task_name"),
            "task_template": payload.get("task_template"),
            "difficulty": payload.get("difficulty"),
            "tags": payload.get("tags") or [],
            "optimal_steps": payload.get("optimal_steps"),
        },
        "official_policy": "No separate policy document is provided in AndroidWorld; the official task metadata and task class source define the task and evaluator-visible success criteria for this case.",
        "evaluator_description": {
            "task_class": payload.get("class_name"),
            "task_module": payload.get("module"),
            "base_class": payload.get("base_class_name"),
        },
        "schema": {
            "task_metadata": {
                "task_name": payload.get("task_name"),
                "difficulty": payload.get("difficulty"),
                "tags": payload.get("tags") or [],
                "optimal_steps": payload.get("optimal_steps"),
            },
        },
        "trace_schema": {
            "episodes_per_record": 1,
            "artifacts": [
                "device state",
                "system state",
                "checkpoint artifacts",
                "observations",
                "actions",
                "messages",
                "native evaluator input",
                "native evaluator output",
            ],
        },
        "available_post_run_artifact_types": [
            "post_state",
            "trace",
            "screenshot",
            "tool_log",
            "message",
            "native_evaluator_input",
            "native_evaluator_output",
            "file",
        ],
        "contract_template": {"claim_scope": "native_aligned"},
        "native_sources": [
            {
                "source_ref": payload.get("source_ref"),
                "source_sha256": payload.get("source_sha256"),
            }
        ],
        "raw_case_manifest": dict(manifest),
    }


def _webarena_context(raw_case_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    derived = raw_case_dir / "derived" / "task.json"
    if not derived.exists():
        derived = raw_case_dir / "task.json"
    payload = json.loads(derived.read_text(encoding="utf-8"))
    return {
        "task_text": {
            "task_id": payload.get("task_id"),
            "sites": payload.get("sites") or [],
            "start_urls": payload.get("start_urls") or [],
            "intent": payload.get("intent"),
            "intent_template": payload.get("intent_template"),
            "instantiation_dict": payload.get("instantiation_dict") or {},
        },
        "official_policy": "No separate policy document is provided in WebArena-Verified; the official task JSON and evaluator description are the official task/evaluator source for this case unit.",
        "evaluator_description": payload.get("eval") or [],
        "schema": {
            "results_schema": [item.get("results_schema") for item in payload.get("eval") or [] if isinstance(item, Mapping)],
        },
        "trace_schema": {
            "sites": payload.get("sites") or [],
            "start_urls": payload.get("start_urls") or [],
        },
        "available_post_run_artifact_types": [
            "native evaluator output",
            "browser artifact",
            "network trace",
            "file",
            "structured output",
        ],
        "contract_template": {"claim_scope": "native_aligned"},
        "native_sources": [{"source_ref": ref} for ref in list(manifest.get("source_refs") or [])],
        "raw_case_manifest": dict(manifest),
    }


def _workarena_context(raw_case_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    helper = raw_case_dir / "derived" / "selected_task_source.json"
    payload = json.loads(helper.read_text(encoding="utf-8"))
    return {
        "task_text": {
            "benchmark": "WorkArena",
            "task_id": payload.get("task_id"),
            "task_category": payload.get("task_category"),
            "task_class": payload.get("class_name"),
        },
        "official_policy": "No separate policy document is provided in WorkArena; the official task class source, task configs, and env.task.validate(page, chat_messages) semantics define the native task requirements.",
        "evaluator_description": {
            "validator": "env.task.validate(page, chat_messages)",
            "task_class": payload.get("class_name"),
            "task_module": payload.get("module"),
            "base_class": payload.get("base_class_name"),
        },
        "schema": {
            "task_configs": payload.get("config_files") or [],
            "task_category": payload.get("task_category"),
        },
        "trace_schema": {
            "episodes_per_record": 1,
            "artifacts": [
                "browser state",
                "task trajectory",
                "validator inputs",
                "validator outputs",
                "structured final output",
            ],
        },
        "available_post_run_artifact_types": [
            "browser_artifact",
            "post_state",
            "trace",
            "native_evaluator_input",
            "native_evaluator_output",
            "structured_output",
            "file",
        ],
        "contract_template": {"claim_scope": "native_aligned"},
        "native_sources": [
            {
                "source_ref": payload.get("source_ref"),
                "source_sha256": payload.get("source_sha256"),
            }
        ],
        "raw_case_manifest": dict(manifest),
    }


def _tau3_context(raw_case_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    derived = raw_case_dir / "derived" / "task.json"
    if not derived.exists():
        derived = raw_case_dir / "task.json"
    policy_file = raw_case_dir / "official" / "policy.md"
    if not policy_file.exists():
        policy_file = raw_case_dir / "policy.md"
    payload = json.loads(derived.read_text(encoding="utf-8"))
    policy = policy_file.read_text(encoding="utf-8")
    instructions = payload.get("user_scenario", {}).get("instructions") or {}
    evaluation = payload.get("evaluation_criteria") or {}
    return {
        "task_text": {
            "domain": instructions.get("domain"),
            "task_instructions": instructions.get("task_instructions"),
            "reason_for_call": instructions.get("reason_for_call"),
            "known_info": instructions.get("known_info"),
            "unknown_info": instructions.get("unknown_info"),
        },
        "official_policy": policy,
        "evaluator_description": {"actions": evaluation.get("actions") or []},
        "schema": {
            "description": payload.get("description"),
            "reward_basis": evaluation.get("reward_basis") or [],
        },
        "trace_schema": {
            "communicate_info": evaluation.get("communicate_info") or [],
            "nl_assertions": evaluation.get("nl_assertions"),
        },
        "available_post_run_artifact_types": [
            "traces",
            "backend state",
            "tool records",
            "policy-relevant records",
            "identity-resolution evidence",
        ],
        "contract_template": {"claim_scope": "native_aligned"},
        "native_sources": [{"source_ref": ref} for ref in list(manifest.get("source_refs") or [])],
        "raw_case_manifest": dict(manifest),
    }
