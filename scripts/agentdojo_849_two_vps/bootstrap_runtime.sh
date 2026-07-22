#!/usr/bin/env bash
set -euo pipefail

# Idempotent, non-secret bootstrap for one AgentDojo remaining-849 VPS.
# The OpenRouter credential and formal namespace leaves are intentionally not
# created here; those are separate post-verification steps.

if [[ "$(id -u)" -ne 0 ]]; then
  echo "bootstrap_runtime.sh must run as root" >&2
  exit 2
fi

controller_public_key=${CONTROLLER_PUBLIC_KEY:?CONTROLLER_PUBLIC_KEY is required}
agentdojo_commit=a75aba7631d3ca5fb7ab938965c97ead2f9ff84b
agentdojo_tree=3c74b60f2bad4ff321d864e0c0483f256cc8f8d2
wheel_name=agentdojo-0.1.35-py3-none-any.whl
wheel_sha256=364bea4219716b716bf639f504d195943f7f6a5535d312ca41d7098704a2affd
base=/srv/agentdojo-full
repo=${base}/repo
upstream=${base}/agentdojo-upstream-v0.1.35
wheel_dir=${base}/tooling/wheels

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl git jq rsync tmux python3 python3-pip python3-venv build-essential

getent group agentdojo-blind >/dev/null || groupadd --system agentdojo-blind
if ! id benchmark >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash benchmark
fi
if ! id agentdojo-monitor >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash agentdojo-monitor
fi
usermod -a -G agentdojo-blind benchmark
usermod -a -G agentdojo-blind agentdojo-monitor

install -d -m 0700 -o benchmark -g benchmark /home/benchmark/.ssh
auth_file=/home/benchmark/.ssh/authorized_keys
if [[ ! -f "${auth_file}" ]] || ! grep -Fqx -- "${controller_public_key}" "${auth_file}"; then
  printf '%s\n' "${controller_public_key}" >> "${auth_file}"
fi
chown benchmark:benchmark "${auth_file}"
chmod 0600 "${auth_file}"

install -d -m 0755 -o root -g root "${base}"
install -d -m 0755 -o benchmark -g benchmark "${repo}"
install -d -m 0700 -o benchmark -g benchmark "${base}/secrets"
install -d -m 0755 -o root -g root "${base}/runtime-state" "${base}/sealed" "${base}/blind-monitor"
install -d -m 0755 -o root -g root \
  "${base}/sealed/raw" "${base}/sealed/failed-attempts" "${base}/sealed/retrieval-snapshots"
install -d -m 0755 -o root -g root "${base}/tooling"
install -d -m 0755 -o benchmark -g benchmark "${wheel_dir}"

if [[ ! -d "${upstream}/.git" ]]; then
  git clone --quiet https://github.com/ethz-spylab/agentdojo.git "${upstream}"
fi
git -C "${upstream}" fetch --quiet --tags origin
git -C "${upstream}" checkout --quiet --detach "${agentdojo_commit}"
observed_commit=$(git -C "${upstream}" rev-parse HEAD)
observed_tree=$(git -C "${upstream}" rev-parse 'HEAD^{tree}')
observed_dirty=$(git -C "${upstream}" status --porcelain)
if [[ "${observed_commit}" != "${agentdojo_commit}" || "${observed_tree}" != "${agentdojo_tree}" || -n "${observed_dirty}" ]]; then
  echo "pinned AgentDojo checkout verification failed" >&2
  exit 3
fi
chown -R benchmark:benchmark "${upstream}"

wheel_path=${wheel_dir}/${wheel_name}
if [[ ! -f "${wheel_path}" ]]; then
  runuser -u benchmark -- python3 -m pip download --no-deps --only-binary=:all: \
    --dest "${wheel_dir}" 'agentdojo==0.1.35'
fi
observed_wheel_sha256=$(sha256sum "${wheel_path}" | awk '{print $1}')
if [[ "${observed_wheel_sha256}" != "${wheel_sha256}" ]]; then
  echo "pinned AgentDojo wheel verification failed" >&2
  exit 4
fi

printf '%s\n' 'BOOTSTRAP_RUNTIME_READY'
