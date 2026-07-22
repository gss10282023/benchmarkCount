#!/usr/bin/env bash
set -euo pipefail

# Run this script from the extracted, immutable upload bundle. It intentionally
# performs draft generation only: there is no benchmark runner or score command.
BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKET_ROOT="$BUNDLE_ROOT/experiments/case_packets_extensions/miniwob_remaining22/miniwob"
OUTPUT_ROOT="${OUTPUT_ROOT:-$BUNDLE_ROOT/results/namespaces/miniwob_remaining22_bg0143_v1/drafts/draft_vps_gpt56_11way_20260718}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -x "$(command -v codex 2>/dev/null || true)" ]]; then
  echo "ERROR: codex CLI is not available on PATH." >&2
  exit 2
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: Python executable not found: $PYTHON_BIN" >&2
  exit 2
fi

CASE_COUNT="$(find "$PACKET_ROOT" -mindepth 2 -maxdepth 2 -name case_packet.md -type f | wc -l | tr -d ' ')"
if [[ "$CASE_COUNT" != "22" ]]; then
  echo "ERROR: expected 22 case packets, found $CASE_COUNT." >&2
  exit 2
fi

"$PYTHON_BIN" -c 'import jsonschema, requests, yaml' >/dev/null

if [[ -e "$OUTPUT_ROOT/_batch_results.jsonl" || -e "$OUTPUT_ROOT/_batch_summary.json" ]]; then
  echo "ERROR: output root already contains a prior batch ledger: $OUTPUT_ROOT" >&2
  echo "Choose a fresh OUTPUT_ROOT; this launcher will not mix two draft runs." >&2
  exit 2
fi

mkdir -p "$OUTPUT_ROOT"

"$PYTHON_BIN" - "$BUNDLE_ROOT" "$OUTPUT_ROOT" <<'PY'
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

bundle_root = Path(sys.argv[1]).resolve()
output_root = Path(sys.argv[2]).resolve()
frozen_inputs = [
    "neurips_ed_track_minimal/checklist_guardrails.py",
    "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md",
    "neurips_ed_track_minimal/schemas/case_checklist.schema.json",
    "neurips_ed_track_minimal/templates/case_checklist.template.yaml",
    "neurips_ed_track_minimal/scripts/checklist_validator.py",
    "neurips_ed_track_minimal/scripts/draft_case_checklist.py",
    "neurips_ed_track_minimal/scripts/run_draft_batch.py",
]

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

packet_root = bundle_root / "experiments/case_packets_extensions/miniwob_remaining22/miniwob"
packet_files = sorted(path for path in packet_root.rglob("*") if path.is_file())
payload = {
    "schema_version": "miniwob_remaining22_draft_launch.v1",
    "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "bundle_root": str(bundle_root),
    "output_root": str(output_root),
    "draft_only": True,
    "benchmark_executed": False,
    "score_executed": False,
    "provider": "codex",
    "model": "gpt-5.6-sol",
    "reasoning_effort": "max",
    "regular_max_parallel": 11,
    "oversized_max_parallel": 11,
    "packet_case_count": 22,
    "packet_file_count": len(packet_files),
    "packet_tree_sha256": hashlib.sha256(
        "".join(
            f"{path.relative_to(bundle_root).as_posix()}\0{sha256(path)}\n"
            for path in packet_files
        ).encode("utf-8")
    ).hexdigest(),
    "frozen_input_sha256": {
        item: sha256(bundle_root / item) for item in frozen_inputs
    },
    "codex_version": subprocess.run(
        ["codex", "--version"], capture_output=True, text=True, check=False
    ).stdout.strip(),
    "python_version": sys.version,
}
(output_root / "_launch_provenance.json").write_text(
    json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
PY

set +e
PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" \
  "$BUNDLE_ROOT/neurips_ed_track_minimal/scripts/run_draft_batch.py" \
  --case-packet-root "$PACKET_ROOT" \
  --output-root "$OUTPUT_ROOT" \
  --provider codex \
  --model gpt-5.6-sol \
  --reasoning-effort max \
  --max-parallel 11 \
  --large-max-parallel 11 \
  --token-budgets 12000,16000,20000 \
  --sort-by size \
  --codex-sandbox read-only \
  2>&1 | tee "$OUTPUT_ROOT/_launcher.log"
BATCH_STATUS="${PIPESTATUS[0]}"
set -e

"$PYTHON_BIN" - "$OUTPUT_ROOT" "$BATCH_STATUS" <<'PY'
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

output_root = Path(sys.argv[1]).resolve()
status = int(sys.argv[2])
path = output_root / "_launch_provenance.json"
payload = json.loads(path.read_text(encoding="utf-8"))
payload["finished_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
payload["batch_exit_code"] = status
payload["benchmark_executed"] = False
payload["score_executed"] = False
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

exit "$BATCH_STATUS"
