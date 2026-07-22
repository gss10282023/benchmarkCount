#!/usr/bin/env bash
set -euo pipefail

# Run as root after the controller has synchronized src/, schemas/, configs/,
# pyproject.toml and uv.lock into /srv/agentdojo-full/repo.

if [[ "$(id -u)" -ne 0 ]]; then
  echo "install_synced_runtime.sh must run as root" >&2
  exit 2
fi

base=/srv/agentdojo-full
repo=${base}/repo
wheel=${base}/tooling/wheels/agentdojo-0.1.35-py3-none-any.whl

test -f "${repo}/pyproject.toml"
test -f "${repo}/uv.lock"
test -f "${wheel}"
chown -R benchmark:benchmark "${repo}"

if [[ ! -x "${repo}/.venv/bin/python" ]]; then
  runuser -u benchmark -- python3 -m venv "${repo}/.venv"
fi
runuser -u benchmark -- "${repo}/.venv/bin/python" -m pip install --disable-pip-version-check -q --upgrade pip
# The formal wheel/RECORD closure requires RECORD to contain only the wheel's
# hashed files plus the single unhashed RECORD row.  pip's default bytecode
# compilation appends unhashed pyc rows, so all formal installs use --no-compile.
runuser -u benchmark -- env PYTHONDONTWRITEBYTECODE=1 "${repo}/.venv/bin/python" -m pip install --no-compile --disable-pip-version-check -q "${wheel}"
runuser -u benchmark -- env PYTHONDONTWRITEBYTECODE=1 "${repo}/.venv/bin/python" -m pip install --no-compile --disable-pip-version-check -q -e "${repo}"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${repo}/src" "${repo}/.venv/bin/python" - <<'PY'
import importlib.metadata
import agentdojo
import evidence_system
assert importlib.metadata.version("agentdojo") == "0.1.35"
print("SYNCED_RUNTIME_READY")
PY
