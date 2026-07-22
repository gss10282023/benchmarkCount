#!/usr/bin/env bash
set -euo pipefail
unset PYTHONHOME PYTHONOPTIMIZE PYTHONPATH VIRTUAL_ENV

# Strict, offline validation of the official WebArena-Verified v1.2.3
# evaluator. Produces a machine-readable receipt on the provisioned host.

readonly INSTALL_ROOT="/opt/webarena-verified/v1.2.3"
readonly SOURCE_DIR="${INSTALL_ROOT}/source"
readonly BROWSER_DIR="${INSTALL_ROOT}/ms-playwright"
readonly RUNTIME_DIR="${INSTALL_ROOT}/runtime"
readonly TASK_CONTRACT_INDEX="${RUNTIME_DIR}/webarena_verified_task_contract_index.json"
readonly VALIDATION_DIR="${INSTALL_ROOT}/validation"
readonly INSTALLED_SCRIPTS_DIR="${INSTALL_ROOT}/scripts"
readonly PROVISION_SCRIPT="${INSTALLED_SCRIPTS_DIR}/provision_webarena_verified_v1_2_3.sh"
readonly VALIDATION_SCRIPT="${INSTALLED_SCRIPTS_DIR}/validate_webarena_verified_v1_2_3.sh"
readonly OFFICIAL_SCORER_SCRIPT="${INSTALLED_SCRIPTS_DIR}/webarena_verified_official_scorer.py"
readonly RUNNER_COMMIT="dce04686a56253aefba7b18a4fa0937cf1dc987b"
readonly RUNNER_TREE="8feabebb86b035004a0a242f13c5ee7bd1f8c627"
readonly RUNNER_ROOT="/opt/webarena-runner/${RUNNER_COMMIT}"
readonly RUNNER_SOURCE_DIR="${RUNNER_ROOT}/source"
readonly RUNNER_VENV="${RUNNER_SOURCE_DIR}/.venv"
readonly RUNNER_REQUIREMENTS_INPUT="${INSTALLED_SCRIPTS_DIR}/webarena_runner_requirements.in"
readonly RUNNER_REQUIREMENTS_LOCK="${INSTALLED_SCRIPTS_DIR}/webarena_runner_requirements.lock"
readonly OFFICIAL_COMMIT="6473f72db5dcefc97b5725b59e734504edc28a21"
readonly OFFICIAL_IMAGE="ghcr.io/servicenow/webarena-verified@sha256:d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
readonly EXPECTED_RAW_DATASET_SHA256="d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
readonly EXPECTED_NORMALIZED_DATASET_SHA256="10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
readonly EXPECTED_RUNTIME_URLS_SHA256="0b54e748bfed53d23852cb0d0f2b54b8a405b8e035b560ff86f3632e7c84f673"
readonly EXPECTED_AGENT_INPUTS_SHA256="d125ad7cf9627d9b9151153eaba20ecd85451899a2e4b70ecdd46510d0775a8e"
readonly EXPECTED_TASK_CONTRACT_INDEX_SHA256="32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
readonly EXPECTED_RUNNER_REQUIREMENTS_INPUT_SHA256="9f3c386d771ae3d556795a15433a30774049ba5b27df006049d3bba4e9e6b2fe"
readonly EXPECTED_RUNNER_REQUIREMENTS_LOCK_SHA256="b1763680fe08f816345c271dbec467661f0aa9cfa9ade79c3694eea6e2b430b4"
readonly EXPECTED_RUNNER_UPSTREAM_REQUIREMENTS_SHA256="86db3ff7932398742f9d567a230592b2843704660ed2220748d26b59e4d06bf2"
readonly EXPECTED_RUNNER_RAW_TASKS_SHA256="7b50386fd69163dbc05d615d834df4c6ed2c35596e97a1b10d17451c02537652"
readonly EXPECTED_RUNNER_FREEZE_SHA256="8a8c82c9dbb98ceaf98331c890823c4e2c755a653e4aa43aece4d34c80b37055"

: "${WEBARENA_SERVER_ID:?WEBARENA_SERVER_ID is required for an identity-bound receipt}"
: "${WEBARENA_VPS_ADDRESS:?WEBARENA_VPS_ADDRESS is required for an identity-bound receipt}"

rm -rf "${VALIDATION_DIR}"
install -d -m 0755 \
  "${VALIDATION_DIR}/dataset" \
  "${VALIDATION_DIR}/retrieval/108" \
  "${VALIDATION_DIR}/navigation-pass/44" \
  "${VALIDATION_DIR}/navigation-strict/44" \
  "${VALIDATION_DIR}/navigation-fail/44" \
  "${VALIDATION_DIR}/runner"

[[ "$(git -C "${SOURCE_DIR}" rev-parse HEAD)" == "${OFFICIAL_COMMIT}" ]]
[[ -f "${PROVISION_SCRIPT}" && -f "${VALIDATION_SCRIPT}" && -f "${OFFICIAL_SCORER_SCRIPT}" ]]
[[ "$(git -C "${RUNNER_SOURCE_DIR}" rev-parse HEAD)" == "${RUNNER_COMMIT}" ]]
[[ "$(git -C "${RUNNER_SOURCE_DIR}" rev-parse 'HEAD^{tree}')" == "${RUNNER_TREE}" ]]
[[ -x "${RUNNER_VENV}/bin/python" ]]
[[ ! -e "${RUNNER_SOURCE_DIR}/agent/prompts/jsons" ]]
echo "${EXPECTED_RAW_DATASET_SHA256}  ${SOURCE_DIR}/assets/dataset/webarena-verified.json" | sha256sum -c -
echo "${EXPECTED_RUNTIME_URLS_SHA256}  ${RUNTIME_DIR}/webarena_verified_runtime_urls.json" | sha256sum -c -
echo "${EXPECTED_AGENT_INPUTS_SHA256}  ${RUNTIME_DIR}/webarena_verified_agent_inputs_full_812.json" | sha256sum -c -
echo "${EXPECTED_TASK_CONTRACT_INDEX_SHA256}  ${TASK_CONTRACT_INDEX}" | sha256sum -c -
echo "${EXPECTED_RUNNER_REQUIREMENTS_INPUT_SHA256}  ${RUNNER_REQUIREMENTS_INPUT}" | sha256sum -c -
echo "${EXPECTED_RUNNER_REQUIREMENTS_LOCK_SHA256}  ${RUNNER_REQUIREMENTS_LOCK}" | sha256sum -c -
echo "${EXPECTED_RUNNER_UPSTREAM_REQUIREMENTS_SHA256}  ${RUNNER_SOURCE_DIR}/requirements.txt" | sha256sum -c -
echo "${EXPECTED_RUNNER_RAW_TASKS_SHA256}  ${RUNNER_SOURCE_DIR}/config_files/test.raw.json" | sha256sum -c -

"${SOURCE_DIR}/.venv/bin/python" - "${RUNTIME_DIR}/webarena_verified_agent_inputs_full_812.json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert isinstance(payload, list) and len(payload) == 812
assert sorted(int(item["task_id"]) for item in payload) == list(range(812))
assert all(set(item) == {"intent", "intent_template_id", "sites", "start_urls", "task_id"} for item in payload)
PY

"${SOURCE_DIR}/.venv/bin/python" - "${TASK_CONTRACT_INDEX}" <<'PY'
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert set(payload) == {
    "benchmark",
    "entries",
    "official_commit",
    "raw_tag_dataset_sha256",
    "schema_version",
    "source_sha256",
    "split",
    "task_count",
    "version",
    "visibility",
}
assert payload["schema_version"] == "webarena_verified_task_contract_index/v1"
assert payload["benchmark"] == "WebArena-Verified"
assert payload["version"] == "v1.2.3"
assert payload["split"] == "full"
assert payload["task_count"] == 812
assert payload["visibility"] == "controller_only"
assert payload["official_commit"] == "6473f72db5dcefc97b5725b59e734504edc28a21"
assert payload["raw_tag_dataset_sha256"] == (
    "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
)
assert payload["source_sha256"] == (
    "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
)

entries = payload["entries"]
assert isinstance(entries, list) and len(entries) == 812
assert [entry["task_id"] for entry in entries] == list(range(812))
assert Counter(entry["task_revision"] for entry in entries) == {2: 793, 3: 14, 4: 5}
hex_digest = re.compile(r"[0-9a-f]{64}").fullmatch
allowed_evaluators = {"AgentResponseEvaluator", "NetworkEventEvaluator"}
allowed_task_types = {"MUTATE", "NAVIGATE", "RETRIEVE"}
entry_fields = {
    "agent_input_sha256",
    "case_packet_sha256",
    "evaluator_names_in_order",
    "intent_template_id",
    "required_run_artifacts",
    "sites",
    "task_id",
    "task_revision",
    "task_type",
}
for entry in entries:
    assert set(entry) == entry_fields
    assert entry["task_revision"] in {2, 3, 4}
    assert entry["task_type"] in allowed_task_types
    assert isinstance(entry["intent_template_id"], int)
    assert isinstance(entry["sites"], list) and entry["sites"]
    assert all(isinstance(site, str) and site for site in entry["sites"])
    assert entry["required_run_artifacts"] == ["agent_response.json", "network.har"]
    evaluator_names = entry["evaluator_names_in_order"]
    assert isinstance(evaluator_names, list) and evaluator_names
    assert set(evaluator_names) <= allowed_evaluators
    assert evaluator_names[0] == "AgentResponseEvaluator"
    assert hex_digest(entry["agent_input_sha256"])
    assert hex_digest(entry["case_packet_sha256"])

# This controller contract may name evaluators, but must not embed any gold
# answer or evaluator payload that could accidentally enter a model prompt.
for forbidden_key in {
    "actual",
    "actual_normalized",
    "answer",
    "assertion_msgs",
    "error_msg",
    "eval",
    "evaluator_config",
    "expected",
    "gold",
    "reference_answer",
}:
    assert not any(f'"{forbidden_key}"' in json.dumps(entry, sort_keys=True) for entry in entries)
PY

"${SOURCE_DIR}/.venv/bin/webarena-verified" dataset-get \
  --output "${VALIDATION_DIR}/dataset/host-dataset-get.json"
docker run --rm \
  -v "${VALIDATION_DIR}/dataset:/output" \
  "${OFFICIAL_IMAGE}" \
  dataset-get --output /output/docker-dataset-get.json

echo "${EXPECTED_NORMALIZED_DATASET_SHA256}  ${VALIDATION_DIR}/dataset/host-dataset-get.json" | sha256sum -c -
echo "${EXPECTED_NORMALIZED_DATASET_SHA256}  ${VALIDATION_DIR}/dataset/docker-dataset-get.json" | sha256sum -c -
cmp "${VALIDATION_DIR}/dataset/host-dataset-get.json" "${VALIDATION_DIR}/dataset/docker-dataset-get.json"

cp "${SOURCE_DIR}/examples/agent_logs/demo/108/agent_response.json" "${VALIDATION_DIR}/retrieval/108/agent_response.json"
cp "${SOURCE_DIR}/examples/agent_logs/demo/108/network.har" "${VALIDATION_DIR}/retrieval/108/network.har"
docker run --rm \
  -v "${VALIDATION_DIR}/retrieval:/output" \
  -v "${SOURCE_DIR}/examples/configs:/configs:ro" \
  "${OFFICIAL_IMAGE}" \
  eval-tasks --task-ids 108 --output-dir /output --config /configs/config.demo.json

cat >"${VALIDATION_DIR}/navigation-pass/44/agent_response.json" <<'JSON'
{
  "task_type": "NAVIGATE",
  "status": "SUCCESS",
  "retrieved_data": null,
  "error_details": null
}
JSON

cat >"${VALIDATION_DIR}/navigation-fail/44/agent_response.json" <<'JSON'
{
  "task_type": "RETRIEVE",
  "status": "SUCCESS",
  "retrieved_data": null,
  "error_details": null
}
JSON

cp "${VALIDATION_DIR}/navigation-pass/44/agent_response.json" \
  "${VALIDATION_DIR}/navigation-strict/44/agent_response.json"

"${SOURCE_DIR}/.venv/bin/python" - "${VALIDATION_DIR}" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
har = {
    "log": {
        "version": "1.2",
        "creator": {"name": "Playwright", "version": "1.56.0"},
        "entries": [
            {
                "startedDateTime": "2026-07-16T00:00:00.000Z",
                "time": 1.0,
                "request": {
                    "method": "GET",
                    "url": "http://localhost:8012/dashboard/todos",
                    "httpVersion": "HTTP/1.1",
                    "cookies": [],
                    "headers": [
                        {"name": "accept", "value": "text/html,application/xhtml+xml"},
                        {"name": "sec-fetch-dest", "value": "document"},
                        {"name": "sec-fetch-mode", "value": "navigate"},
                        {"name": "sec-fetch-user", "value": "?1"},
                    ],
                    "queryString": [],
                    "headersSize": -1,
                    "bodySize": -1,
                },
                "response": {
                    "status": 200,
                    "statusText": "OK",
                    "httpVersion": "HTTP/1.1",
                    "cookies": [],
                    "headers": [],
                    "content": {
                        "size": 31,
                        "mimeType": "text/html",
                        "text": "<html><body>todos</body></html>",
                    },
                    "redirectURL": "",
                    "headersSize": -1,
                    "bodySize": 0,
                },
                "cache": {},
                "timings": {"send": 0, "wait": 1, "receive": 0},
            }
        ],
    }
}
for name in ("navigation-pass", "navigation-fail"):
    (root / name / "44" / "network.har").write_text(json.dumps(har, indent=2) + "\n", encoding="utf-8")
PY

PLAYWRIGHT_BROWSERS_PATH="${BROWSER_DIR}" "${SOURCE_DIR}/.venv/bin/python" - \
  "${VALIDATION_DIR}/navigation-strict/44/network.har" <<'PY'
from pathlib import Path
import sys

from playwright.sync_api import Browser, sync_playwright

har_path = Path(sys.argv[1])
original_new_context = Browser.new_context

def full_har_context(browser, *args, **kwargs):
    kwargs["record_har_path"] = str(har_path)
    kwargs["record_har_content"] = "embed"
    kwargs["record_har_mode"] = "full"
    return original_new_context(browser, *args, **kwargs)

Browser.new_context = full_har_context
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        context.route(
            "http://127.0.0.1:8023/**",
            lambda route: route.fulfill(
                status=200,
                content_type="text/html",
                body="<html><body>todos</body></html>",
            ),
        )
        page = context.new_page()
        page.goto("http://127.0.0.1:8023/dashboard/todos")
        context.close()
        browser.close()
finally:
    Browser.new_context = original_new_context

assert har_path.is_file() and har_path.stat().st_size > 0
PY

for fixture in navigation-pass navigation-fail; do
  docker run --rm \
    -v "${VALIDATION_DIR}/${fixture}:/output" \
    -v "${SOURCE_DIR}/examples/configs:/configs:ro" \
    "${OFFICIAL_IMAGE}" \
    eval-tasks --task-ids 44 --output-dir /output --config /configs/config.demo.json
done

python3 "${OFFICIAL_SCORER_SCRIPT}" \
  --task-id 44 \
  --task-revision 2 \
  --output-root "${VALIDATION_DIR}/navigation-strict" \
  --config "${RUNTIME_DIR}/webarena_verified_runtime_urls.json" \
  --task-contract-index "${TASK_CONTRACT_INDEX}" \
  --summary-output "${VALIDATION_DIR}/navigation-strict/44/eval_summary.strict.json" \
  >"${VALIDATION_DIR}/navigation-strict/44/scorer.stdout.log"

(
  export SHOPPING="http://127.0.0.1:7770"
  export SHOPPING_ADMIN="http://127.0.0.1:7780/admin"
  export REDDIT="http://127.0.0.1:9999"
  export GITLAB="http://127.0.0.1:8023"
  export WIKIPEDIA="http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing"
  export MAP="http://127.0.0.1:3030"
  export HOMEPAGE="http://127.0.0.1:4399"
  cd "${RUNNER_SOURCE_DIR}"
  "${RUNNER_VENV}/bin/python" scripts/generate_test_data.py
)

"${INSTALL_ROOT}/uv-bootstrap/bin/uv" pip freeze \
  --python "${RUNNER_VENV}/bin/python" \
  >"${VALIDATION_DIR}/runner/requirements.freeze.txt"
echo "${EXPECTED_RUNNER_FREEZE_SHA256}  ${VALIDATION_DIR}/runner/requirements.freeze.txt" | sha256sum -c -

SHOPPING="http://127.0.0.1:7770" \
SHOPPING_ADMIN="http://127.0.0.1:7780/admin" \
REDDIT="http://127.0.0.1:9999" \
GITLAB="http://127.0.0.1:8023" \
WIKIPEDIA="http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing" \
MAP="http://127.0.0.1:3030" \
HOMEPAGE="http://127.0.0.1:4399" \
PLAYWRIGHT_BROWSERS_PATH="${BROWSER_DIR}" \
  "${RUNNER_VENV}/bin/python" - "${VALIDATION_DIR}/runner" "${RUNNER_SOURCE_DIR}" <<'PY'
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
from threading import Thread

import agent.prompts.prompt_constructor  # noqa: F401
import browser_env
import llms.lm_config  # noqa: F401
from playwright.sync_api import Browser, sync_playwright

output_dir = Path(sys.argv[1])
repo_dir = Path(sys.argv[2])
har_path = output_dir / "script_browser_env.network.har"
task_config_path = output_dir / "script_browser_env.task.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = b"<html><title>runner integration</title><button>OK</button></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
Thread(target=server.serve_forever, daemon=True).start()
task_config_path.write_text(
    json.dumps({"start_url": f"http://127.0.0.1:{server.server_port}/"}) + "\n",
    encoding="utf-8",
)

original_new_context = Browser.new_context


def full_har_context(browser: Browser, *args: object, **kwargs: object) -> object:
    kwargs["record_har_path"] = str(har_path)
    kwargs["record_har_content"] = "embed"
    kwargs["record_har_mode"] = "full"
    return original_new_context(browser, *args, **kwargs)


Browser.new_context = full_har_context  # type: ignore[method-assign]
environment = browser_env.ScriptBrowserEnv(
    headless=True,
    observation_type="accessibility_tree",
    current_viewport_only=True,
    viewport_size={"width": 1280, "height": 720},
)
try:
    observation, info = environment.reset(options={"config_file": str(task_config_path)})
    assert "button" in str(observation["text"]).lower()
    assert str(info["page"].url).startswith("http://127.0.0.1:")
    environment.context.close()
finally:
    environment.close()
    Browser.new_context = original_new_context  # type: ignore[method-assign]
    server.shutdown()

har = json.loads(har_path.read_text(encoding="utf-8"))
entries = har["log"]["entries"]
assert entries
assert all("text" in entry["response"]["content"] for entry in entries)
assert all(
    {"startedDateTime", "time", "request", "response", "cache", "timings"}.issubset(entry)
    for entry in entries
)

numeric_configs = sorted(
    (path for path in (repo_dir / "config_files").glob("*.json") if path.stem.isdigit()),
    key=lambda path: int(path.stem),
)
assert len(numeric_configs) == 812
assert [int(path.stem) for path in numeric_configs] == list(range(812))
for expected_task_id, path in enumerate(numeric_configs):
    assert int(json.loads(path.read_text(encoding="utf-8"))["task_id"]) == expected_task_id

tracked_changes = subprocess.check_output(
    ["git", "-C", str(repo_dir), "status", "--porcelain", "--untracked-files=no"],
    text=True,
)
assert not tracked_changes.strip()

with sync_playwright() as playwright:
    browser_path = Path(playwright.chromium.executable_path)
    browser = playwright.chromium.launch(headless=True)
    chromium_version = browser.version
    browser.close()

result = {
    "status": "verified",
    "runner_repository": "https://github.com/web-arena-x/webarena.git",
    "runner_commit": subprocess.check_output(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"], text=True
    ).strip(),
    "runner_tree": subprocess.check_output(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD^{tree}"], text=True
    ).strip(),
    "runner_python_version": platform.python_version(),
    "runner_package_version": importlib.metadata.version("webarena"),
    "runner_playwright_version": importlib.metadata.version("playwright"),
    "runner_chromium_version": chromium_version,
    "runner_chromium_executable": str(browser_path),
    "runner_chromium_executable_sha256": sha256(browser_path),
    "generated_config_count": len(numeric_configs),
    "upstream_generated_prompt_absent": not (repo_dir / "agent" / "prompts" / "jsons").exists(),
    "script_browser_env_import": True,
    "script_browser_env_accessibility_tree": True,
    "script_browser_env_full_embedded_har": True,
    "har_creator": har["log"]["creator"],
    "integration_har_sha256": sha256(har_path),
}
(output_dir / "runner_validation.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, indent=2, sort_keys=True))
PY

PLAYWRIGHT_BROWSERS_PATH="${BROWSER_DIR}" "${SOURCE_DIR}/.venv/bin/python" - "${VALIDATION_DIR}" <<'PY'
from __future__ import annotations

import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from webarena_verified.core.evaluation.evaluators.agent_response_evaluator import AgentResponseEvaluator
from webarena_verified.core.evaluation.evaluators.network_event_evaluator import NetworkEventEvaluator
from webarena_verified.core.utils.checksum import compute_evaluator_checksum

root = Path(sys.argv[1])

def load_result(name: str, task_id: int) -> dict:
    return json.loads((root / name / str(task_id) / "eval_result.json").read_text(encoding="utf-8"))

retrieval = load_result("retrieval", 108)
navigation_pass = load_result("navigation-pass", 44)
navigation_fail = load_result("navigation-fail", 44)
strict_scorer_summary = json.loads(
    (root / "navigation-strict" / "44" / "eval_summary.strict.json").read_text(encoding="utf-8")
)

assert retrieval["status"] == "success" and retrieval["score"] == 1.0
assert navigation_pass["status"] == "success" and navigation_pass["score"] == 1.0
assert {item["evaluator_name"] for item in navigation_pass["evaluators_results"]} == {
    "AgentResponseEvaluator",
    "NetworkEventEvaluator",
}
assert all(item["score"] == 1.0 for item in navigation_pass["evaluators_results"])
assert navigation_fail["status"] == "failure" and navigation_fail["score"] == 0.0
fail_scores = {item["evaluator_name"]: item["score"] for item in navigation_fail["evaluators_results"]}
assert fail_scores == {"AgentResponseEvaluator": 0.0, "NetworkEventEvaluator": 1.0}
assert strict_scorer_summary["scorer_status"] == "success"
assert strict_scorer_summary["integrity_verified"] is True
assert strict_scorer_summary["score"] == 1.0
assert strict_scorer_summary["task_contract_index_sha256"] == (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
assert strict_scorer_summary["summary_contains_private_evaluator_payload"] is False
evaluator_checksum = compute_evaluator_checksum()
assert evaluator_checksum == "35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e"
for result in (retrieval, navigation_pass, navigation_fail):
    assert result["webarena_verified_version"] == "1.2.3"
    assert result["webarena_verified_evaluator_checksum"] == evaluator_checksum
    assert result["webarena_verified_data_checksum"] == "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"

with sync_playwright() as p:
    browser_path = Path(p.chromium.executable_path)
    browser = p.chromium.launch(headless=True)
    chromium_version = browser.version
    browser.close()

freeze_path = root / "requirements.freeze.txt"
freeze = subprocess.check_output(
    [
        "/opt/webarena-verified/v1.2.3/uv-bootstrap/bin/uv",
        "pip",
        "freeze",
        "--python",
        sys.executable,
    ],
    text=True,
)
freeze_path.write_text(freeze, encoding="utf-8")

dpkg_inventory_path = root / "dpkg-package-inventory.tsv"
dpkg_inventory = subprocess.check_output(
    ["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${Architecture}\n"],
    text=True,
)
dpkg_inventory_lines = sorted(line for line in dpkg_inventory.splitlines() if line)
dpkg_inventory_path.write_text("\n".join(dpkg_inventory_lines) + "\n", encoding="utf-8")

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def command(*argv: str) -> str:
    return subprocess.check_output(argv, text=True).strip()

runner_validation_path = root / "runner" / "runner_validation.json"
runner_validation = json.loads(runner_validation_path.read_text(encoding="utf-8"))
runner_freeze_path = root / "runner" / "requirements.freeze.txt"
assert runner_validation["status"] == "verified"
assert runner_validation["runner_commit"] == "dce04686a56253aefba7b18a4fa0937cf1dc987b"
assert runner_validation["runner_tree"] == "8feabebb86b035004a0a242f13c5ee7bd1f8c627"
assert runner_validation["runner_python_version"] == "3.11.13"
assert runner_validation["runner_playwright_version"] == "1.56.0"
assert runner_validation["generated_config_count"] == 812
assert runner_validation["upstream_generated_prompt_absent"] is True
assert sha256(runner_freeze_path) == "8a8c82c9dbb98ceaf98331c890823c4e2c755a653e4aa43aece4d34c80b37055"
assert runner_validation["runner_chromium_executable_sha256"] == sha256(browser_path)

image_reference = (
    "ghcr.io/servicenow/webarena-verified@"
    "sha256:d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
)
image_repo_digests = json.loads(
    command("docker", "image", "inspect", image_reference, "--format", "{{json .RepoDigests}}")
)
receipt = {
    "schema_version": "webarena_verified_step20_environment_receipt/v3",
    "status": "verified",
    "server_id": os.environ["WEBARENA_SERVER_ID"],
    "vps_address": os.environ["WEBARENA_VPS_ADDRESS"],
    "host": platform.node(),
    "ssh_host_ed25519_fingerprint": command(
        "ssh-keygen", "-lf", "/etc/ssh/ssh_host_ed25519_key.pub", "-E", "sha256"
    ).split()[1],
    "architecture": platform.machine(),
    "os_release": Path("/etc/os-release").read_text(encoding="utf-8"),
    "official_repository": "https://github.com/ServiceNow/webarena-verified.git",
    "official_tag": "v1.2.3",
    "official_commit": command("git", "-C", "/opt/webarena-verified/v1.2.3/source", "rev-parse", "HEAD"),
    "raw_dataset_sha256": sha256(Path("/opt/webarena-verified/v1.2.3/source/assets/dataset/webarena-verified.json")),
    "normalized_dataset_sha256": sha256(root / "dataset" / "host-dataset-get.json"),
    "runtime_urls_sha256": sha256(Path("/opt/webarena-verified/v1.2.3/runtime/webarena_verified_runtime_urls.json")),
    "official_agent_inputs_sha256": sha256(Path("/opt/webarena-verified/v1.2.3/runtime/webarena_verified_agent_inputs_full_812.json")),
    "official_agent_input_count": 812,
    "task_contract_index_path": "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_task_contract_index.json",
    "task_contract_index_sha256": sha256(
        Path("/opt/webarena-verified/v1.2.3/runtime/webarena_verified_task_contract_index.json")
    ),
    "original_webarena_runner_repository": runner_validation["runner_repository"],
    "original_webarena_runner_commit": runner_validation["runner_commit"],
    "original_webarena_runner_tree": runner_validation["runner_tree"],
    "original_webarena_runner_source": "/opt/webarena-runner/dce04686a56253aefba7b18a4fa0937cf1dc987b/source",
    "original_webarena_runner_upstream_requirements_sha256": sha256(
        Path("/opt/webarena-runner/dce04686a56253aefba7b18a4fa0937cf1dc987b/source/requirements.txt")
    ),
    "original_webarena_runner_raw_tasks_sha256": sha256(
        Path("/opt/webarena-runner/dce04686a56253aefba7b18a4fa0937cf1dc987b/source/config_files/test.raw.json")
    ),
    "runner_requirements_input_sha256": sha256(
        Path("/opt/webarena-verified/v1.2.3/scripts/webarena_runner_requirements.in")
    ),
    "runner_requirements_lock_sha256": sha256(
        Path("/opt/webarena-verified/v1.2.3/scripts/webarena_runner_requirements.lock")
    ),
    "runner_dependency_freeze_path": str(runner_freeze_path),
    "runner_dependency_freeze_sha256": sha256(runner_freeze_path),
    "runner_python_version": runner_validation["runner_python_version"],
    "runner_package_version": runner_validation["runner_package_version"],
    "runner_playwright_version": runner_validation["runner_playwright_version"],
    "runner_upstream_generated_prompt_absent": runner_validation["upstream_generated_prompt_absent"],
    "runner_generated_config_count": runner_validation["generated_config_count"],
    "runner_chromium_version": runner_validation["runner_chromium_version"],
    "runner_chromium_executable": runner_validation["runner_chromium_executable"],
    "runner_chromium_executable_sha256": runner_validation["runner_chromium_executable_sha256"],
    "provision_script_sha256": sha256(Path("/opt/webarena-verified/v1.2.3/scripts/provision_webarena_verified_v1_2_3.sh")),
    "validation_script_sha256": sha256(Path("/opt/webarena-verified/v1.2.3/scripts/validate_webarena_verified_v1_2_3.sh")),
    "official_scorer_script_sha256": sha256(Path("/opt/webarena-verified/v1.2.3/scripts/webarena_verified_official_scorer.py")),
    "official_evaluator_checksum": evaluator_checksum,
    "uv_lock_sha256": sha256(Path("/opt/webarena-verified/v1.2.3/source/uv.lock")),
    "python_version": platform.python_version(),
    "webarena_verified_version": importlib.metadata.version("webarena-verified"),
    "playwright_version": importlib.metadata.version("playwright"),
    "chromium_version": chromium_version,
    "chromium_executable": str(browser_path),
    "chromium_executable_sha256": sha256(browser_path),
    "dependency_freeze_path": str(freeze_path),
    "dependency_freeze_sha256": sha256(freeze_path),
    "dpkg_package_inventory_path": str(dpkg_inventory_path),
    "dpkg_package_inventory_count": len(dpkg_inventory_lines),
    "dpkg_package_inventory_sha256": sha256(dpkg_inventory_path),
    "docker_version": command("docker", "version", "--format", "{{.Server.Version}}"),
    "docker_compose_version": command("docker", "compose", "version", "--short"),
    "official_evaluator_image": image_reference,
    "official_evaluator_image_id": command(
        "docker", "image", "inspect", image_reference, "--format", "{{.Id}}"
    ),
    "official_evaluator_repo_digests": image_repo_digests,
    "evaluator_modules": {
        "AgentResponseEvaluator": {
            "path": inspect.getfile(AgentResponseEvaluator),
            "sha256": sha256(Path(inspect.getfile(AgentResponseEvaluator))),
        },
        "NetworkEventEvaluator": {
            "path": inspect.getfile(NetworkEventEvaluator),
            "sha256": sha256(Path(inspect.getfile(NetworkEventEvaluator))),
        },
    },
    "legacy_evaluator_importable_in_locked_environment": False,
    "legacy_evaluator_importable_in_official_evaluator_environment": False,
    "legacy_evaluator_present_only_as_unused_runner_source": True,
    "validation": {
        "dataset_host_docker_identical": True,
        "retrieval_task_108_expected_score": 1.0,
        "retrieval_task_108_actual_score": retrieval["score"],
        "navigation_task_44_expected_score": 1.0,
        "navigation_task_44_actual_score": navigation_pass["score"],
        "navigation_task_44_evaluators": sorted(item["evaluator_name"] for item in navigation_pass["evaluators_results"]),
        "negative_control_task_44_expected_score": 0.0,
        "negative_control_task_44_actual_score": navigation_fail["score"],
        "negative_control_per_evaluator": fail_scores,
        "native_aggregate_is_binary_not_browsergym_average": navigation_fail["score"] == 0.0,
        "strict_pinned_scorer_lane": True,
        "strict_scorer_network_har": True,
        "task_contract_index_hash_verified": True,
        "task_contract_index_schema_validated": True,
        "runner_upstream_generated_prompt_absent": runner_validation[
            "upstream_generated_prompt_absent"
        ],
        "playwright_full_embedded_har_injection": True,
        "playwright_chromium_launch": True,
        "original_webarena_runner_imports": runner_validation["script_browser_env_import"],
        "original_webarena_generated_config_count": runner_validation["generated_config_count"],
        "script_browser_env_accessibility_tree": runner_validation[
            "script_browser_env_accessibility_tree"
        ],
        "script_browser_env_full_embedded_har": runner_validation[
            "script_browser_env_full_embedded_har"
        ],
        "runner_and_evaluator_share_chromium_binary": (
            runner_validation["runner_chromium_executable_sha256"] == sha256(browser_path)
        ),
    },
}

try:
    __import__("evaluation_harness")
except ModuleNotFoundError:
    pass
else:
    raise AssertionError("legacy web-arena-x evaluation_harness is importable in locked evaluator environment")

receipt_path = root / "environment_receipt.json"
receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2, sort_keys=True))
PY

echo "validation-status=ok"
