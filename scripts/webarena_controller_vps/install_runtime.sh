#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "install_runtime.sh must run as root." >&2
  exit 2
fi

app_root=/opt/webarena-controller/app
venv_root=/opt/webarena-controller/venv
state_root=/srv/webarena-controller/state
secret_root=/srv/webarena-controller/secrets
unit_root=$app_root/scripts/webarena_controller_vps/systemd

for command in python3 ssh ssh-keyscan ssh-keygen rsync systemctl flock; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "Missing required command: $command" >&2
    exit 2
  }
done
test -f "$app_root/pyproject.toml"
test -f "$app_root/scripts/run_webarena_verified_full.py"
test -f "$app_root/experiments/step20/webarena_verified/jobs/full/index.json"

if ! id -u webarenasvc >/dev/null 2>&1; then
  useradd \
    --system \
    --home-dir /srv/webarena-controller \
    --create-home \
    --shell /usr/sbin/nologin \
    webarenasvc
fi

install -d -m 0755 -o root -g root /opt/webarena-controller "$app_root"
install -d -m 0750 -o webarenasvc -g webarenasvc /srv/webarena-controller
install -d -m 0700 -o webarenasvc -g webarenasvc "$state_root" "$secret_root"

python3 -m venv "$venv_root"
"$venv_root/bin/python" -m pip install --upgrade pip
"$venv_root/bin/python" -m pip install "$app_root"

chown -R root:root "$app_root" "$venv_root"
find "$app_root" -type d -exec chmod 0755 {} +
find "$app_root" -type f -exec chmod 0644 {} +
chmod 0755 \
  "$app_root/scripts/run_webarena_verified_full.py" \
  "$app_root/scripts/webarena_controller_vps/run_controller_service.sh" \
  "$app_root/scripts/webarena_controller_vps/webarena_controller_watch.py" \
  "$app_root/scripts/webarena_controller_vps/install_runtime.sh"

chown -R webarenasvc:webarenasvc \
  "$app_root/results" \
  "$app_root/experiments/step20/webarena_verified"
find "$app_root/results" "$app_root/experiments/step20/webarena_verified" -type d -exec chmod 0700 {} +
find "$app_root/results" "$app_root/experiments/step20/webarena_verified" -type f -exec chmod 0600 {} +

for unit in \
  webarena-controller.service \
  webarena-controller-verify.service \
  webarena-health-watch.service \
  webarena-health-watch.timer \
  webarena-artifact-watch.service \
  webarena-artifact-watch.timer \
  webarena-progress-summary.service \
  webarena-progress-summary.timer; do
  install -m 0644 -o root -g root "$unit_root/$unit" "/etc/systemd/system/$unit"
done

systemctl daemon-reload
systemctl disable webarena-controller.service >/dev/null 2>&1 || true
systemctl enable --now \
  webarena-health-watch.timer \
  webarena-artifact-watch.timer \
  webarena-progress-summary.timer

echo "WebArena controller runtime installed; paid controller remains disabled and inactive."
