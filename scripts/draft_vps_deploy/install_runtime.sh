#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "install_runtime.sh must run as root." >&2
  exit 2
fi

app_root=/opt/neurips-draft/app
package_root=$app_root/neurips_ed_track_minimal
deploy_root=/opt/neurips-draft/deploy
venv_root=/opt/neurips-draft/venv
service_home=/srv/neurips-draft/home

for executable in bash curl python3 codex systemctl systemd-run sudo; do
  if ! command -v "$executable" >/dev/null 2>&1; then
    echo "Missing required executable: $executable" >&2
    exit 2
  fi
done
if [[ ! -f $package_root/requirements.txt ]]; then
  echo "Draft package has not been uploaded to $package_root" >&2
  exit 2
fi
if [[ ! -d $deploy_root/bin ]]; then
  echo "Deployment helpers have not been uploaded to $deploy_root" >&2
  exit 2
fi
if [[ ! -f $deploy_root/apparmor/neurips-codex ]]; then
  echo "Codex AppArmor profile has not been uploaded to $deploy_root/apparmor" >&2
  exit 2
fi
if [[ ! -d $app_root/src/evidence_system ]]; then
  echo "Score runtime source has not been uploaded to $app_root/src/evidence_system" >&2
  exit 2
fi

if ! id -u draftsvc >/dev/null 2>&1; then
  useradd \
    --system \
    --home-dir "$service_home" \
    --create-home \
    --shell /usr/sbin/nologin \
    draftsvc
fi

install -d -m 0755 -o root -g root /opt/neurips-draft "$app_root" "$deploy_root"
install -d -m 0750 -o draftsvc -g draftsvc /srv/neurips-draft /srv/neurips-draft/jobs "$service_home"
install -d -m 0700 -o draftsvc -g draftsvc "$service_home/.codex"
install -d -m 0700 -o draftsvc -g draftsvc "$service_home/.claude"
install -d -m 0750 -o draftsvc -g draftsvc \
  /srv/neurips-score \
  /srv/neurips-score/jobs \
  /srv/neurips-score/runtime \
  /srv/neurips-score/runtime/codex_homes \
  /srv/neurips-score/runtime/tmp \
  /srv/neurips-score/runtime/pycache

if [[ ! -x /usr/local/bin/claude ]]; then
  claude_code_version=${CLAUDE_CODE_VERSION:-2.1.170}
  sudo -H -u draftsvc bash -c \
    'curl -fsSL https://claude.ai/install.sh | bash -s -- "$1"' \
    _ "$claude_code_version"
  claude_user_bin=$service_home/.local/bin/claude
  if [[ ! -x $claude_user_bin ]]; then
    echo "Claude Code installer did not create $claude_user_bin" >&2
    exit 2
  fi
  install -m 0755 -o root -g root "$(readlink -f "$claude_user_bin")" /usr/local/bin/claude
fi
/usr/local/bin/claude --version
claude_help=$(/usr/local/bin/claude --help)
for required_flag in --effort --json-schema --no-session-persistence --safe-mode; do
  if [[ $claude_help != *"$required_flag"* ]]; then
    echo "Installed Claude Code does not support required flag: $required_flag" >&2
    exit 2
  fi
done

python3 -m venv "$venv_root"
"$venv_root/bin/python" -m pip install --upgrade pip
"$venv_root/bin/python" -m pip install --requirement "$package_root/requirements.txt"

install -m 0755 "$deploy_root/bin/neurips-draft-batch" /usr/local/bin/neurips-draft-batch
install -m 0755 "$deploy_root/bin/neurips-draft-init" /usr/local/bin/neurips-draft-init
install -m 0755 "$deploy_root/bin/neurips-draft-submit" /usr/local/bin/neurips-draft-submit
install -m 0755 "$deploy_root/bin/neurips-draft-status" /usr/local/bin/neurips-draft-status
install -m 0755 "$deploy_root/bin/neurips-draft-login" /usr/local/bin/neurips-draft-login
install -m 0755 "$deploy_root/bin/neurips-score-batch" /usr/local/bin/neurips-score-batch
install -m 0755 "$deploy_root/bin/neurips-score-claude-login" /usr/local/bin/neurips-score-claude-login
install -m 0755 "$deploy_root/bin/neurips-score-init" /usr/local/bin/neurips-score-init
install -m 0755 "$deploy_root/bin/neurips-score-submit" /usr/local/bin/neurips-score-submit
install -m 0755 "$deploy_root/bin/neurips-score-status" /usr/local/bin/neurips-score-status

# Ubuntu 24.04 restricts unprivileged user namespaces through AppArmor. Codex's
# Linux read-only sandbox needs one, so grant userns only to its native binary
# instead of disabling the system-wide restriction.
if command -v apparmor_parser >/dev/null 2>&1; then
  install -m 0644 "$deploy_root/apparmor/neurips-codex" /etc/apparmor.d/neurips-codex
  apparmor_parser -r /etc/apparmor.d/neurips-codex
fi

if [[ ! -e /etc/neurips-draft.env ]]; then
  install -m 0644 /dev/null /etc/neurips-draft.env
  printf '%s\n' \
    'DRAFT_MODEL=gpt-5.4' \
    'DRAFT_REASONING_EFFORT=xhigh' \
    'DRAFT_MAX_PARALLEL=8' \
    'DRAFT_LARGE_MAX_PARALLEL=2' \
    'DRAFT_MAX_ALLOWED_PARALLEL=72' \
    'DRAFT_CODEX_TIMEOUT_SECONDS=1800' \
    'DRAFT_LARGE_CODEX_TIMEOUT_SECONDS=3600' \
    >>/etc/neurips-draft.env
fi

if [[ ! -e /etc/neurips-score.env ]]; then
  install -m 0644 /dev/null /etc/neurips-score.env
  printf '%s\n' \
    'SCORE_MODEL=gpt-5.4' \
    'SCORE_REASONING_EFFORT=xhigh' \
    'SCORE_MAX_PARALLEL=1' \
    'SCORE_MAX_ALLOWED_PARALLEL=36' \
    'SCORE_CODEX_TIMEOUT_SECONDS=1800' \
    'SCORE_MAX_ATTEMPTS=2' \
    'SCORE_MAX_RUN_ATTEMPTS=2' \
    'SCORE_MAX_INPUT_FILES=200000' \
    'SCORE_MAX_INPUT_BYTES=107374182400' \
    'SCORE_MAX_SINGLE_FILE_BYTES=5368709120' \
    'SCORE_MIN_FREE_BYTES=21474836480' \
    >>/etc/neurips-score.env
fi

ensure_env_default() {
  local path=$1
  local key=$2
  local value=$3
  if ! grep -q "^${key}=" "$path"; then
    printf '%s=%s\n' "$key" "$value" >>"$path"
  fi
}

ensure_env_default /etc/neurips-score.env SCORE_CLAUDE_MODEL sonnet
ensure_env_default /etc/neurips-score.env SCORE_CLAUDE_REASONING_EFFORT high
ensure_env_default /etc/neurips-score.env SCORE_CLAUDE_MAX_PARALLEL 1
ensure_env_default /etc/neurips-score.env SCORE_CLAUDE_MAX_ALLOWED_PARALLEL 72
ensure_env_default /etc/neurips-score.env SCORE_CLAUDE_TIMEOUT_SECONDS 1800

chown -R root:root "$app_root" "$deploy_root"
find "$app_root" "$deploy_root" -type d -exec chmod 0755 {} +
find "$app_root" "$deploy_root" -type f -exec chmod 0644 {} +
find "$deploy_root/bin" -type f -exec chmod 0755 {} +
chmod 0755 "$deploy_root/install_runtime.sh"

"$venv_root/bin/python" -m py_compile \
  "$package_root/checklist_guardrails.py" \
  "$package_root/scripts/checklist_validator.py" \
  "$package_root/scripts/draft_case_checklist.py" \
  "$package_root/scripts/run_draft_batch.py" \
  "$package_root/scripts/run_score_batch.py" \
  "$package_root/scripts/score_evidence_with_codex.py" \
  "$package_root/scripts/score_evidence_with_claude.py"

echo "Draft + score runtime installed."
echo "Codex login: neurips-draft-login"
echo "Claude score login: neurips-score-claude-login"
