from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from evidence_system.adapters import webarena_verified_official_scorer as scorer
from evidence_system.webarena_fault_injection import (
    FAULT_KINDS,
    validate_fault_receipt,
)
from evidence_system.webarena_fault_injection_remote import (
    EXPECTED_AGENT_BINDINGS,
    INVALID_PLACEHOLDER_SHA256,
    REMOTE_EXECUTION_CONFIRMATION,
    REMOTE_GOLDEN_ADAPTER_ROOT,
    RemoteFaultExecutionError,
    RemoteFaultExecutor,
    build_remote_fault_plan,
    execute_remote_fault_matrix,
    load_remote_fault_bindings,
    write_remote_fault_plan,
)
from evidence_system import webarena_fault_injection_remote as remote_module
from evidence_system.webarena_sites import atomic_write_json, load_site_lock


ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "configs/infra.yaml"
SITE_LOCK = ROOT / "configs/webarena_verified_sites.lock.json"


@dataclass
class _State:
    machine_id: str
    site_running: bool = True
    container_serial: int = 1
    lock_held: bool = False
    reset_calls: int = 0
    stop_should_fail: bool = False
    provider_key_present: bool = False

    @property
    def container_id(self) -> str:
        return f"{self.machine_id}-container-{self.container_serial}"


class _FakeController:
    def __init__(self, state: _State) -> None:
        self.state = state

    def status(self, sites):
        assert sites == ["shopping"]
        row = {
            "site": "shopping",
            "ok": self.state.site_running,
            "container": {
                "container_id": self.state.container_id,
                "running": self.state.site_running,
            },
            "sentinels": [{"name": "homepage", "ok": self.state.site_running}],
        }
        return {
            "schema_version": "webarena_verified_site_status/v1",
            "status": "pass" if self.state.site_running else "fail",
            "machine_id": self.state.machine_id,
            "sites": [row],
        }

    def _acquire_exclusive_lock(self, *, owner):
        assert owner["fault_kind"] == "site_outage"
        assert not self.state.lock_held
        self.state.lock_held = True
        return "opaque-lock-token"

    def _release_exclusive_lock(self, token):
        assert token == "opaque-lock-token"
        assert self.state.lock_held
        self.state.lock_held = False

    def reset_slot(self, *, identity, sites, receipt_path):
        assert sites == ["shopping"]
        self.state.reset_calls += 1
        before = self.state.container_id
        self.state.site_running = True
        self.state.container_serial += 1
        payload = {
            "schema_version": "webarena_verified_slot_reset_receipt/v1",
            "status": "pass",
            "slot": {
                "slot_id": identity.slot_id,
                "task_id": identity.task_id,
                "agent_id": identity.agent_id,
                "attempt_id": identity.attempt_id,
                "seed": identity.seed,
            },
            "machine": {"machine_id": self.state.machine_id},
            "sites": [
                {
                    "site": "shopping",
                    "ok": True,
                    "before": {"container_id": before},
                    "after": {
                        "container_id": self.state.container_id,
                        "running": True,
                    },
                    "sentinels": [{"name": "homepage", "ok": True}],
                }
            ],
        }
        atomic_write_json(receipt_path, payload)
        return payload

    def verify_login(self):
        return {
            "status": "pass",
            "generated_state_file_count": 5,
            "validated_cookie_count": 9,
            "sensitive_state_retained": False,
        }


class _FakeRunner:
    def __init__(self, state: _State) -> None:
        self.state = state
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, timeout):
        del timeout
        command = tuple(str(item) for item in argv)
        self.calls.append(command)
        joined = " ".join(command)
        if command[:3] == ("docker", "stop", "--time"):
            if self.state.stop_should_fail:
                return subprocess.CompletedProcess(command, 1, "", "stop failed")
            self.state.site_running = False
            return subprocess.CompletedProcess(command, 0, self.state.container_id + "\n", "")
        if "provider_key_present" in joined:
            payload = {"provider_key_present": self.state.provider_key_present}
        elif "worker_process_count" in joined and "ps" in joined:
            payload = {"worker_process_count": 0}
        elif "wv-login-fault-" in joined:
            payload = {
                "probe_kind": "official_auto_login",
                "wrong_target_kind": "closed_loopback_port",
                "auto_login_exit_nonzero": True,
                "auto_login_returncode": 1,
                "storage_state_created": False,
                "state_file_count": 0,
                "auth_folder_removed": True,
                "stdout_sha256": "a" * 64,
                "stderr_sha256": "b" * 64,
                "stdout_bytes": 0,
                "stderr_bytes": 12,
            }
        elif "non_billable_key_auth" in joined:
            payload = {
                "probe_kind": "openrouter_transport",
                "endpoint_kind": "non_billable_key_auth",
                "worker_exit_nonzero": True,
                "child_returncode": 17,
                "provider_http_status": 401,
                "model_completion_received": False,
                "credential_scope": "injected_placeholder_child_only",
                "response_body_sha256": "c" * 64,
                "response_body_bytes": 24,
                "parent_key_present_before": False,
                "parent_key_present_after": False,
                "placeholder_child_destroyed": True,
                "parent_environment_unchanged": True,
            }
        elif "wv-evaluator-fault-" in joined:
            payload = {
                "probe_kind": "pinned_official_scorer",
                "scorer_exit_code": 2,
                "scorer_status": "error",
                "official_evaluation_completed": False,
                "integrity_verified": False,
                "mutated_input_is_copy": True,
                "fault_stdout_sha256": "d" * 64,
                "fault_stderr_sha256": "e" * 64,
                "golden_recovery_exit_code": 0,
                "golden_recovery_scorer_status": "success",
                "golden_recovery_official_evaluation_completed": True,
                "golden_recovery_integrity_verified": True,
                "recovery_stdout_sha256": "f" * 64,
                "recovery_stderr_sha256": "1" * 64,
                "baseline_hash_before": "2" * 64,
                "baseline_hash_after": "2" * 64,
                "baseline_artifact_hash_unchanged": True,
                "corrupt_copy_quarantined": True,
                "temporary_workspace_deleted": True,
                "remote_scorer_source_sha256": _scorer_sha(),
            }
        else:  # pragma: no cover - catches accidental new remote operations.
            raise AssertionError(f"unexpected fake remote command: {command!r}")
        return subprocess.CompletedProcess(command, 0, json.dumps(payload) + "\n", "")


def _scorer_sha() -> str:
    import hashlib

    return hashlib.sha256(Path(scorer.__file__).read_bytes()).hexdigest()


def _executor(tmp_path: Path, *, stop_should_fail: bool = False):
    binding = load_remote_fault_bindings(INFRA)[0]
    state = _State(binding.target.machine_id, stop_should_fail=stop_should_fail)
    runner = _FakeRunner(state)
    controller = _FakeController(state)
    executor = RemoteFaultExecutor(
        binding=binding,
        site_lock=load_site_lock(SITE_LOCK),
        receipts_root=tmp_path / "receipts",
        runner=runner,
        controller=controller,
    )
    return executor, state, runner


def test_real_plan_is_exact_three_by_four_and_is_read_only(tmp_path: Path) -> None:
    plan = build_remote_fault_plan(
        infra_config_path=INFRA,
        receipts_root=tmp_path / "remote",
    )

    assert plan["status"] == "planned"
    assert plan["remote_execution_performed"] is False
    assert plan["receipt_count"] == 12
    assert plan["paid_model_calls_planned"] == 0
    assert plan["provider_probe_endpoint_kind"] == "non_billable_key_auth"
    assert plan["provider_probe_spec_source"].endswith("/api-keys/get-current-key")
    assert plan["real_credential_input_supported"] is False
    assert plan["dotenv_loading_supported"] is False
    assert plan["scheduler_quiescence_required"] is True
    assert plan["concurrent_pilot_or_full_run_allowed"] is False
    assert REMOTE_GOLDEN_ADAPTER_ROOT.endswith(
        "/golden-parity-v1/controller_only/response_only_success/adapter"
    )
    assert len(plan["infra_config_sha256"]) == 64
    assert len(plan["executor_source_sha256"]) == 64
    assert plan["official_evaluator_image"].startswith(
        "ghcr.io/servicenow/webarena-verified@sha256:"
    )
    core = {key: value for key, value in plan.items() if key != "integrity"}
    from evidence_system.core.hashing import sha256_object

    assert plan["integrity"]["core_sha256"] == sha256_object(core)
    assert [(row["machine_id"], row["fault_kind"]) for row in plan["rows"]] == [
        (machine_id, kind)
        for machine_id in EXPECTED_AGENT_BINDINGS
        for kind in FAULT_KINDS
    ]
    output = tmp_path / "plan.json"
    write_remote_fault_plan(output, plan)
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert json.loads(output.read_text(encoding="utf-8")) == plan


def test_bindings_use_exact_agent_routes_and_sha256_ssh_fingerprints() -> None:
    bindings = load_remote_fault_bindings(INFRA)

    assert len(bindings) == 3
    assert [binding.target.machine_id for binding in bindings] == list(
        EXPECTED_AGENT_BINDINGS
    )
    assert [binding.agent_id for binding in bindings] == list(
        EXPECTED_AGENT_BINDINGS.values()
    )
    assert all(
        binding.ssh_host_fingerprint.startswith("SHA256:") for binding in bindings
    )
    assert all(binding.target.benchmark_config["sync_dotenv"] is False for binding in bindings)


def test_default_remote_runner_passes_the_exact_locked_fingerprint(
    monkeypatch, tmp_path: Path
) -> None:
    binding = load_remote_fault_bindings(INFRA)[0]
    captured = {}

    def fake_verified(**kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(["ssh"], 0, "ok\n", "")

    monkeypatch.setattr(
        "evidence_system.webarena_fault_injection_remote.run_verified_ssh_argv",
        fake_verified,
    )
    executor = RemoteFaultExecutor(
        binding=binding,
        site_lock=load_site_lock(SITE_LOCK),
        receipts_root=tmp_path,
        controller=_FakeController(_State(binding.target.machine_id)),
    )
    result = executor._verified_remote(["true"], 7)

    assert result.returncode == 0
    assert captured["host"] == binding.target.ssh_host
    assert captured["expected_ed25519_fingerprint"] == binding.ssh_host_fingerprint
    assert captured["argv"] == ["true"]
    assert captured["timeout"] == 7


@pytest.mark.parametrize("kind", FAULT_KINDS)
def test_each_real_executor_path_writes_two_private_evidence_files_and_receipt(
    tmp_path: Path, kind: str
) -> None:
    executor, state, runner = _executor(tmp_path)
    path = executor.run_fault(kind)

    receipt = json.loads(path.read_text(encoding="utf-8"))
    validate_fault_receipt(receipt)
    assert receipt["execution_mode"] == "remote_real"
    assert receipt["fault_kind"] == kind
    assert receipt["observed_semantics"]["execution_status"] == "INFRA_EXCLUDED"
    assert receipt["observed_semantics"]["evidence_label"] == "UNRESOLVE"
    assert receipt["safety"]["paid_model_calls"] == 0
    assert len(receipt["evidence"]) == 2
    for descriptor in receipt["evidence"]:
        evidence_path = executor.receipts_root / descriptor["relative_reference"]
        assert evidence_path.is_file()
        assert stat.S_IMODE(evidence_path.stat().st_mode) == 0o600
    if kind == "site_outage":
        assert state.site_running is True
        assert state.reset_calls == 1
        assert any(command[:2] == ("docker", "stop") for command in runner.calls)


def test_site_outage_always_slot_resets_even_if_stop_observation_fails(
    tmp_path: Path,
) -> None:
    executor, state, _ = _executor(tmp_path, stop_should_fail=True)

    with pytest.raises(RemoteFaultExecutionError, match="successful recovery"):
        executor.run_fault("site_outage")

    assert state.site_running is True
    assert state.reset_calls == 1
    assert state.lock_held is False
    assert not (
        executor.receipts_root
        / executor.machine_id
        / "site_outage"
        / "receipt.json"
    ).exists()


def test_any_remote_fault_refuses_to_start_if_provider_env_contains_a_key(
    tmp_path: Path,
) -> None:
    executor, state, runner = _executor(tmp_path)
    state.provider_key_present = True

    with pytest.raises(RemoteFaultExecutionError, match="contains a provider key"):
        executor.run_fault("site_outage")

    assert state.site_running is True
    assert state.reset_calls == 0
    assert not any(command[:2] == ("docker", "stop") for command in runner.calls)


def test_invalid_api_uses_only_non_billable_auth_endpoint_and_persists_no_value(
    tmp_path: Path,
) -> None:
    executor, _, runner = _executor(tmp_path)
    path = executor.run_fault("invalid_placeholder_api_key")
    serialized = path.read_text(encoding="utf-8")
    private = (
        executor.receipts_root
        / "private"
        / executor.machine_id
        / "invalid_placeholder_api_key"
    )
    serialized += "".join(
        item.read_text(encoding="utf-8") for item in private.glob("*.json")
    )

    assert INVALID_PLACEHOLDER_SHA256 in serialized
    assert "evidence-system-known-invalid-auth-probe-v1" not in serialized
    assert "chat/completions" not in " ".join(" ".join(call) for call in runner.calls)
    assert "api/v1/key" in " ".join(" ".join(call) for call in runner.calls)


def test_login_failure_wrapper_really_runs_bad_target_and_removes_state(
    tmp_path: Path,
) -> None:
    runner = tmp_path / "runner"
    browser_env = runner / "browser_env"
    browser_env.mkdir(parents=True)
    (browser_env / "auto_login.py").write_text(
        """
import os, pathlib, sys
args = sys.argv
folder = pathlib.Path(args[args.index('--auth_folder') + 1])
if os.environ.get('SHOPPING', '').startswith('http://127.0.0.1:1/'):
    raise SystemExit(9)
(folder / 'shopping_state.json').write_text('{}')
""".strip()
        + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            remote_module._LOGIN_FAILURE_SCRIPT,
            str(runner),
            sys.executable,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(completed.stdout.strip())

    assert completed.returncode == 0
    assert payload["auto_login_exit_nonzero"] is True
    assert payload["auto_login_returncode"] == 9
    assert payload["storage_state_created"] is False
    assert payload["auth_folder_removed"] is True
    assert set(payload).isdisjoint({"stdout", "stderr", "cookie", "storage_state"})


def test_evaluator_wrapper_uses_invalid_copy_then_clean_golden_recovery(
    tmp_path: Path,
) -> None:
    controller = tmp_path / "controller"
    module_dir = controller / "src/evidence_system/adapters"
    module_dir.mkdir(parents=True)
    (controller / "src/evidence_system/__init__.py").write_text("", encoding="utf-8")
    (module_dir / "__init__.py").write_text("", encoding="utf-8")
    scorer_source = module_dir / "webarena_verified_official_scorer.py"
    scorer_source.write_text(
        """
import argparse, json, pathlib
p=argparse.ArgumentParser()
p.add_argument('--task-id'); p.add_argument('--task-revision')
p.add_argument('--output-root'); p.add_argument('--config')
p.add_argument('--task-contract-index'); p.add_argument('--summary-output')
a=p.parse_args()
har=json.loads((pathlib.Path(a.output_root)/'0/network.har').read_text())
ok=bool(har.get('log'))
summary={
 'scorer_status':'success' if ok else 'error',
 'official_evaluation_completed':ok,
 'integrity_verified':ok,
}
pathlib.Path(a.summary_output).write_text(json.dumps(summary))
raise SystemExit(0 if ok else 2)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    golden = tmp_path / "golden" / "0"
    golden.mkdir(parents=True)
    (golden / "agent_response.json").write_text("{}\n", encoding="utf-8")
    (golden / "network.har").write_text(
        json.dumps({"log": {"version": "1.2", "entries": [{}]}}) + "\n",
        encoding="utf-8",
    )
    runtime_config = tmp_path / "runtime.json"
    runtime_config.write_text("{}\n", encoding="utf-8")
    contract = tmp_path / "contract.json"
    contract.write_text(
        json.dumps({"entries": [{"task_id": 0, "task_revision": 1}]}) + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            remote_module._EVALUATOR_ERROR_SCRIPT,
            str(controller),
            sys.executable,
            str(golden.parent),
            str(runtime_config),
            str(contract),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(completed.stdout.strip())

    assert completed.returncode == 0
    assert payload["scorer_exit_code"] == 2
    assert payload["scorer_status"] == "error"
    assert payload["integrity_verified"] is False
    assert payload["golden_recovery_exit_code"] == 0
    assert payload["golden_recovery_scorer_status"] == "success"
    assert payload["golden_recovery_integrity_verified"] is True
    assert payload["baseline_artifact_hash_unchanged"] is True
    assert payload["temporary_workspace_deleted"] is True


def test_matrix_execution_with_measured_test_doubles_produces_exact_twelve(
    tmp_path: Path,
) -> None:
    states: dict[str, _State] = {}
    runners: dict[str, _FakeRunner] = {}

    def runner_factory(binding):
        state = _State(binding.target.machine_id)
        runner = _FakeRunner(state)
        states[binding.target.machine_id] = state
        runners[binding.target.machine_id] = runner
        return runner

    def controller_factory(binding, _site_lock, _runner):
        return _FakeController(states[binding.target.machine_id])

    receipts = tmp_path / "remote"
    acceptance = tmp_path / "acceptance.json"
    result = execute_remote_fault_matrix(
        infra_config_path=INFRA,
        site_lock_path=SITE_LOCK,
        receipts_root=receipts,
        acceptance_output=acceptance,
        confirmation=REMOTE_EXECUTION_CONFIRMATION,
        runner_factory=runner_factory,
        controller_factory=controller_factory,
    )

    assert result.acceptance["status"] == "pass"
    assert result.acceptance["formal_step20_fault_gate_satisfied"] is True
    assert result.acceptance["counts"]["validated_receipts"] == 12
    assert result.acceptance["counts"]["paid_model_calls"] == 0
    assert len(result.receipt_paths) == 12
    assert result.failures == ()
    assert all(state.site_running for state in states.values())
    assert all(state.reset_calls == 1 for state in states.values())


def test_matrix_failure_is_blocked_and_public_failure_persists_no_exception_text(
    tmp_path: Path,
) -> None:
    states: dict[str, _State] = {}

    def runner_factory(binding):
        state = _State(
            binding.target.machine_id,
            stop_should_fail=binding.target.machine_id == "webarena-gpt54-ord",
        )
        states[binding.target.machine_id] = state
        return _FakeRunner(state)

    def controller_factory(binding, _site_lock, _runner):
        return _FakeController(states[binding.target.machine_id])

    receipts = tmp_path / "remote"
    result = execute_remote_fault_matrix(
        infra_config_path=INFRA,
        site_lock_path=SITE_LOCK,
        receipts_root=receipts,
        acceptance_output=tmp_path / "acceptance.json",
        confirmation=REMOTE_EXECUTION_CONFIRMATION,
        runner_factory=runner_factory,
        controller_factory=controller_factory,
    )

    assert result.acceptance["status"] == "blocked"
    assert result.acceptance["formal_step20_fault_gate_satisfied"] is False
    assert len(result.failures) == 1
    failure_path = (
        receipts
        / "private/webarena-gpt54-ord/site_outage/execution_failure.json"
    )
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    assert failure["error_type"] == "RemoteFaultExecutionError"
    assert failure["exception_message_persisted"] is False
    assert "error_message" not in failure
    assert stat.S_IMODE(failure_path.stat().st_mode) == 0o600
    assert states["webarena-gpt54-ord"].site_running is True


def test_matrix_requires_explicit_confirmation_and_never_overwrites(tmp_path: Path) -> None:
    with pytest.raises(RemoteFaultExecutionError, match="not explicitly armed"):
        execute_remote_fault_matrix(
            infra_config_path=INFRA,
            site_lock_path=SITE_LOCK,
            receipts_root=tmp_path / "remote",
            acceptance_output=tmp_path / "acceptance.json",
            confirmation="no",
            runner_factory=lambda _binding: (_ for _ in ()).throw(AssertionError()),
        )

    root = tmp_path / "existing"
    existing = root / "machine" / "site_outage" / "receipt.json"
    existing.parent.mkdir(parents=True)
    existing.write_text("{}\n", encoding="utf-8")
    with pytest.raises(RemoteFaultExecutionError, match="overwrite"):
        execute_remote_fault_matrix(
            infra_config_path=INFRA,
            site_lock_path=SITE_LOCK,
            receipts_root=root,
            acceptance_output=tmp_path / "acceptance.json",
            confirmation=REMOTE_EXECUTION_CONFIRMATION,
            runner_factory=lambda _binding: (_ for _ in ()).throw(AssertionError()),
        )


def test_remote_executor_source_has_no_dotenv_loader_or_billable_completion_url() -> None:
    source = (
        ROOT / "src/evidence_system/webarena_fault_injection_remote.py"
    ).read_text(encoding="utf-8")

    assert "load_project_dotenv" not in source
    assert "chat/completions" not in source
    assert "OPENROUTER_API_KEY" in source  # Presence-only environment check.
    assert "api/v1/key" in source
    assert "sk-or-v1-" not in source
