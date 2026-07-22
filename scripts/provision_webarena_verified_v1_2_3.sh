#!/usr/bin/env bash
set -euo pipefail
unset PYTHONHOME PYTHONOPTIMIZE PYTHONPATH VIRTUAL_ENV

# Reproducible WebArena-Verified v1.2.3 evaluator/browser-runner provisioning.
# This intentionally does not deploy the benchmark websites. It installs the
# pinned evaluator, Docker runtime, Playwright/Chromium runtime, and the
# project-selected, commit-pinned original-WebArena driver needed to execute
# the agent loop. WebArena-Verified does not itself ship an agent runner.

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

readonly INSTALL_ROOT="/opt/webarena-verified/v1.2.3"
readonly SOURCE_DIR="${INSTALL_ROOT}/source"
readonly BROWSER_DIR="${INSTALL_ROOT}/ms-playwright"
readonly BOOTSTRAP_VENV="${INSTALL_ROOT}/uv-bootstrap"
readonly INSTALLED_SCRIPTS_DIR="${INSTALL_ROOT}/scripts"
readonly OFFICIAL_REPO="https://github.com/ServiceNow/webarena-verified.git"
readonly OFFICIAL_TAG="v1.2.3"
readonly OFFICIAL_COMMIT="6473f72db5dcefc97b5725b59e734504edc28a21"
readonly OFFICIAL_IMAGE="ghcr.io/servicenow/webarena-verified@sha256:d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
readonly DOCKER_IO_VERSION="29.1.3-0ubuntu3~24.04.2"
readonly DOCKER_COMPOSE_VERSION="2.40.3+ds1-0ubuntu1~24.04.1"
readonly PYTHON_VENV_VERSION="3.12.3-0ubuntu2.1"
readonly UV_VERSION="0.9.0"
readonly SYSTEM_PYTHON="/usr/bin/python3.12"
readonly EXPECTED_UV_LOCK_SHA256="890024b5fab3f4565391d7113377dcebe1ec07b25bbe5309a464e80a85df2fcf"
readonly EXPECTED_RAW_DATASET_SHA256="d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
readonly RUNNER_REPO="https://github.com/web-arena-x/webarena.git"
readonly RUNNER_COMMIT="dce04686a56253aefba7b18a4fa0937cf1dc987b"
readonly RUNNER_TREE="8feabebb86b035004a0a242f13c5ee7bd1f8c627"
readonly RUNNER_ROOT="/opt/webarena-runner/${RUNNER_COMMIT}"
readonly RUNNER_SOURCE_DIR="${RUNNER_ROOT}/source"
readonly RUNNER_PYTHON_ROOT="${RUNNER_ROOT}/python"
readonly RUNNER_VENV="${RUNNER_SOURCE_DIR}/.venv"
readonly RUNNER_PYTHON_VERSION="3.11.13"
readonly RUNNER_REQUIREMENTS_INPUT="${INSTALLED_SCRIPTS_DIR}/webarena_runner_requirements.in"
readonly RUNNER_REQUIREMENTS_LOCK="${INSTALLED_SCRIPTS_DIR}/webarena_runner_requirements.lock"
readonly EXPECTED_RUNNER_REQUIREMENTS_INPUT_SHA256="9f3c386d771ae3d556795a15433a30774049ba5b27df006049d3bba4e9e6b2fe"
readonly EXPECTED_RUNNER_REQUIREMENTS_LOCK_SHA256="b1763680fe08f816345c271dbec467661f0aa9cfa9ade79c3694eea6e2b430b4"
readonly EXPECTED_RUNNER_UPSTREAM_REQUIREMENTS_SHA256="86db3ff7932398742f9d567a230592b2843704660ed2220748d26b59e4d06bf2"
readonly EXPECTED_RUNNER_RAW_TASKS_SHA256="7b50386fd69163dbc05d615d834df4c6ed2c35596e97a1b10d17451c02537652"
readonly EXPECTED_RUNNER_FREEZE_SHA256="8a8c82c9dbb98ceaf98331c890823c4e2c755a653e4aa43aece4d34c80b37055"

if [[ "$(id -u)" != "0" ]]; then
  echo "provisioning must run as root" >&2
  exit 2
fi

if [[ "$(dpkg --print-architecture)" != "amd64" ]]; then
  echo "unsupported architecture: $(dpkg --print-architecture); expected amd64" >&2
  exit 2
fi

# This file exists on the required Ubuntu target.
# shellcheck disable=SC1091
. /etc/os-release
if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then
  echo "unsupported OS: ${PRETTY_NAME:-unknown}; expected Ubuntu 24.04" >&2
  exit 2
fi

apt-get update

for package_version in \
  "docker.io=${DOCKER_IO_VERSION}" \
  "docker-compose-v2=${DOCKER_COMPOSE_VERSION}" \
  "python3-venv=${PYTHON_VENV_VERSION}"
do
  package="${package_version%%=*}"
  version="${package_version#*=}"
  if ! apt-cache madison "${package}" | awk '{print $3}' | grep -Fxq "${version}"; then
    echo "required apt version unavailable: ${package_version}" >&2
    exit 3
  fi
done

apt-get install -y --no-install-recommends \
  "docker.io=${DOCKER_IO_VERSION}" \
  "docker-compose-v2=${DOCKER_COMPOSE_VERSION}" \
  "python3-venv=${PYTHON_VENV_VERSION}" \
  ca-certificates curl git jq

systemctl enable --now docker
docker info >/dev/null

install -d -m 0755 "${INSTALL_ROOT}"
if [[ ! -f "${RUNNER_REQUIREMENTS_INPUT}" || ! -f "${RUNNER_REQUIREMENTS_LOCK}" ]]; then
  echo "missing deployed runner dependency lock under ${INSTALLED_SCRIPTS_DIR}" >&2
  exit 4
fi
echo "${EXPECTED_RUNNER_REQUIREMENTS_INPUT_SHA256}  ${RUNNER_REQUIREMENTS_INPUT}" | sha256sum -c -
echo "${EXPECTED_RUNNER_REQUIREMENTS_LOCK_SHA256}  ${RUNNER_REQUIREMENTS_LOCK}" | sha256sum -c -

if [[ ! -d "${SOURCE_DIR}/.git" ]]; then
  git clone --branch "${OFFICIAL_TAG}" --depth 1 "${OFFICIAL_REPO}" "${SOURCE_DIR}"
fi

if [[ "$(git -C "${SOURCE_DIR}" remote get-url origin)" != "${OFFICIAL_REPO}" ]]; then
  echo "unexpected source origin in ${SOURCE_DIR}" >&2
  exit 4
fi
git -C "${SOURCE_DIR}" fetch --depth 1 origin "refs/tags/${OFFICIAL_TAG}:refs/tags/${OFFICIAL_TAG}"
git -C "${SOURCE_DIR}" checkout --detach "${OFFICIAL_COMMIT}"
if [[ "$(git -C "${SOURCE_DIR}" rev-parse HEAD)" != "${OFFICIAL_COMMIT}" ]]; then
  echo "official commit verification failed" >&2
  exit 4
fi

echo "${EXPECTED_UV_LOCK_SHA256}  ${SOURCE_DIR}/uv.lock" | sha256sum -c -
echo "${EXPECTED_RAW_DATASET_SHA256}  ${SOURCE_DIR}/assets/dataset/webarena-verified.json" | sha256sum -c -

if [[ ! -x "${BOOTSTRAP_VENV}/bin/python" ]]; then
  python3 -m venv "${BOOTSTRAP_VENV}"
fi
"${BOOTSTRAP_VENV}/bin/python" -m pip install --disable-pip-version-check --no-cache-dir --upgrade \
  "pip==24.0" "uv==${UV_VERSION}"

(
  cd "${SOURCE_DIR}"
  "${BOOTSTRAP_VENV}/bin/uv" sync \
    --frozen \
    --python "${SYSTEM_PYTHON}" \
    --no-dev \
    --no-group dev \
    --extra examples
)

install -d -m 0755 "${BROWSER_DIR}"
PLAYWRIGHT_BROWSERS_PATH="${BROWSER_DIR}" \
  "${SOURCE_DIR}/.venv/bin/playwright" install --with-deps chromium

docker pull "${OFFICIAL_IMAGE}"
docker image inspect "${OFFICIAL_IMAGE}" >/dev/null

install -d -m 0755 "${RUNNER_ROOT}" "${RUNNER_PYTHON_ROOT}"
if [[ ! -d "${RUNNER_SOURCE_DIR}/.git" ]]; then
  if [[ -e "${RUNNER_SOURCE_DIR}" ]]; then
    echo "runner source path exists but is not a git checkout: ${RUNNER_SOURCE_DIR}" >&2
    exit 4
  fi
  git clone --filter=blob:none --no-checkout "${RUNNER_REPO}" "${RUNNER_SOURCE_DIR}"
fi
if [[ "$(git -C "${RUNNER_SOURCE_DIR}" remote get-url origin)" != "${RUNNER_REPO}" ]]; then
  echo "unexpected runner source origin in ${RUNNER_SOURCE_DIR}" >&2
  exit 4
fi
git -C "${RUNNER_SOURCE_DIR}" fetch --depth 1 origin "${RUNNER_COMMIT}"
git -C "${RUNNER_SOURCE_DIR}" checkout --detach "${RUNNER_COMMIT}"
if [[ "$(git -C "${RUNNER_SOURCE_DIR}" rev-parse HEAD)" != "${RUNNER_COMMIT}" ]]; then
  echo "project-selected WebArena driver commit verification failed" >&2
  exit 4
fi
if [[ "$(git -C "${RUNNER_SOURCE_DIR}" rev-parse 'HEAD^{tree}')" != "${RUNNER_TREE}" ]]; then
  echo "project-selected WebArena driver tree verification failed" >&2
  exit 4
fi
echo "${EXPECTED_RUNNER_UPSTREAM_REQUIREMENTS_SHA256}  ${RUNNER_SOURCE_DIR}/requirements.txt" | sha256sum -c -
echo "${EXPECTED_RUNNER_RAW_TASKS_SHA256}  ${RUNNER_SOURCE_DIR}/config_files/test.raw.json" | sha256sum -c -

UV_PYTHON_INSTALL_DIR="${RUNNER_PYTHON_ROOT}" \
  "${BOOTSTRAP_VENV}/bin/uv" python install "${RUNNER_PYTHON_VERSION}" --managed-python --no-bin
runner_python="$({
  UV_PYTHON_INSTALL_DIR="${RUNNER_PYTHON_ROOT}" \
    "${BOOTSTRAP_VENV}/bin/uv" python find "${RUNNER_PYTHON_VERSION}" --managed-python
} 2>/dev/null)"
if [[ -z "${runner_python}" || ! -x "${runner_python}" ]]; then
  echo "unable to resolve pinned runner Python ${RUNNER_PYTHON_VERSION}" >&2
  exit 4
fi
if [[ ! -x "${RUNNER_VENV}/bin/python" ]]; then
  "${BOOTSTRAP_VENV}/bin/uv" venv --python "${runner_python}" "${RUNNER_VENV}"
fi
if [[ "$("${RUNNER_VENV}/bin/python" -c 'import platform; print(platform.python_version())')" != "${RUNNER_PYTHON_VERSION}" ]]; then
  echo "runner venv Python version does not match ${RUNNER_PYTHON_VERSION}" >&2
  exit 4
fi
"${BOOTSTRAP_VENV}/bin/uv" pip sync \
  --python "${RUNNER_VENV}/bin/python" \
  --require-hashes \
  --strict \
  "${RUNNER_REQUIREMENTS_LOCK}"
"${BOOTSTRAP_VENV}/bin/uv" pip install \
  --python "${RUNNER_VENV}/bin/python" \
  --no-deps \
  --editable "${RUNNER_SOURCE_DIR}"

# Generated upstream prompt JSON is intentionally absent.  The production
# worker uses a repository-bundled, hash-pinned copy so an untracked generated
# file can never silently change the model protocol.
rm -rf "${RUNNER_SOURCE_DIR}/agent/prompts/jsons"
if [[ -e "${RUNNER_SOURCE_DIR}/agent/prompts/jsons" ]]; then
  echo "upstream-generated runner prompt directory must be absent" >&2
  exit 4
fi

# The hash-pinned dependency lock must resolve to this exact environment, not
# merely install successfully. The validator preserves the same freeze as a
# receipt artifact.
runner_freeze_sha256="$({
  "${BOOTSTRAP_VENV}/bin/uv" pip freeze --python "${RUNNER_VENV}/bin/python" \
    | sha256sum \
    | awk '{print $1}'
})"
if [[ "${runner_freeze_sha256}" != "${EXPECTED_RUNNER_FREEZE_SHA256}" ]]; then
  echo "runner dependency freeze verification failed: ${runner_freeze_sha256}" >&2
  exit 4
fi

ln -sfn "${SOURCE_DIR}/.venv/bin/webarena-verified" /usr/local/bin/webarena-verified-v1.2.3

cat >"${INSTALL_ROOT}/runtime.env" <<EOF
WEBARENA_VERIFIED_HOME=${INSTALL_ROOT}
WEBARENA_VERIFIED_SOURCE=${SOURCE_DIR}
WEBARENA_VERIFIED_IMAGE=${OFFICIAL_IMAGE}
WEBARENA_RUNNER_SOURCE=${RUNNER_SOURCE_DIR}
WEBARENA_RUNNER_PYTHON=${RUNNER_VENV}/bin/python
PLAYWRIGHT_BROWSERS_PATH=${BROWSER_DIR}
EOF
chmod 0644 "${INSTALL_ROOT}/runtime.env"

"${SOURCE_DIR}/.venv/bin/python" - <<'PY'
from importlib.metadata import version

assert version("webarena-verified") == "1.2.3"
assert version("playwright") == "1.56.0"
print("python-package-check=ok")
PY

PLAYWRIGHT_BROWSERS_PATH="${BROWSER_DIR}" "${SOURCE_DIR}/.venv/bin/python" - <<'PY'
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_content("<title>wv-provision-check</title><p>ok</p>")
    assert page.title() == "wv-provision-check"
    print(f"chromium-check=ok version={browser.version}")
    browser.close()
PY

SHOPPING="http://127.0.0.1:7770" \
SHOPPING_ADMIN="http://127.0.0.1:7780/admin" \
REDDIT="http://127.0.0.1:9999" \
GITLAB="http://127.0.0.1:8023" \
WIKIPEDIA="http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing" \
MAP="http://127.0.0.1:3030" \
HOMEPAGE="http://127.0.0.1:4399" \
PLAYWRIGHT_BROWSERS_PATH="${BROWSER_DIR}" \
  "${RUNNER_VENV}/bin/python" - <<'PY'
from importlib.metadata import version
from pathlib import Path
import tempfile

import agent.prompts.prompt_constructor
import browser_env
import llms.lm_config
from playwright.sync_api import sync_playwright

assert version("playwright") == "1.56.0"
with tempfile.TemporaryDirectory() as temporary_directory:
    har_path = Path(temporary_directory) / "runner.har"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            record_har_path=har_path,
            record_har_content="embed",
            record_har_mode="full",
        )
        page = context.new_page()
        page.set_content("<title>webarena-runner-check</title><button>ok</button>")
        assert page.title() == "webarena-runner-check"
        context.close()
        browser.close()
    assert har_path.is_file() and har_path.stat().st_size > 0
print("original-webarena-runner-check=ok")
PY

docker run --rm "${OFFICIAL_IMAGE}" --help >/dev/null
echo "provision-status=ok"
