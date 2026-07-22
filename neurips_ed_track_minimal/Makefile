SHELL := /bin/sh
PYTHON ?= python3

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SCRIPTS := $(ROOT)/scripts

MODEL ?=
PROVIDER ?=
REASONING_EFFORT ?=
MAX_OUTPUT_TOKENS ?=
CODEX_TIMEOUT_SECONDS ?=
CLAUDE_TIMEOUT_SECONDS ?=
SANDBOX ?=
MAX_ATTEMPTS ?=
NATIVE_LABEL_PATH ?=

.DEFAULT_GOAL := help

.PHONY: help check-deps validate smoke draft draft-codex score score-claude score-agentdojo-batch

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make validate' \
	  '  make smoke' \
	  '  Optional override: make ... PYTHON=/path/to/python' \
	  '  make draft CASE_PACKET=/path/to/case_packet.md OUTPUT=/path/to/checklist.yaml [PROVIDER=auto|codex|openai|openrouter] [MODEL=...] [REASONING_EFFORT=...]' \
	  '  make draft-codex CASE_PACKET=/path/to/case_packet.md OUTPUT=/path/to/checklist.yaml [MODEL=gpt-5.4] [REASONING_EFFORT=xhigh] [CODEX_TIMEOUT_SECONDS=1800]' \
	  '  make score CHECKLIST=/path/to/checklist.yaml EVIDENCE_DIR=/path/to/run_artifacts [OUT_PREFIX=/path/to/results/case_score] [MODEL=gpt-5.4] [REASONING_EFFORT=xhigh] [SANDBOX=read-only] [MAX_ATTEMPTS=2] [NATIVE_LABEL_PATH=/path/to/native_label]' \
	  '  make score-claude CHECKLIST=/path/to/checklist.yaml EVIDENCE_DIR=/path/to/run_artifacts [OUT_PREFIX=/path/to/results/case_score] [MODEL=sonnet] [REASONING_EFFORT=high] [CLAUDE_TIMEOUT_SECONDS=1800] [MAX_ATTEMPTS=2]' \
	  '  make score-agentdojo-batch [MODEL=gpt-5.4] [REASONING_EFFORT=xhigh] [PER_KEY_CONCURRENCY=4] [TASKS_PER_KEY=100] [SANDBOX=read-only] [MAX_ATTEMPTS=2] [MAX_RUN_ATTEMPTS=2]' \
	  '  python scripts/checklist_validator.py /path/to/checklist.yaml' \
	  '  python scripts/update_case_locks.py --case-packet /path/to/case_packet.md --checklist /path/to/checklist.yaml'

check-deps:
	@$(PYTHON) -c 'import importlib.util, sys; missing = [m for m in ("requests", "yaml", "jsonschema") if importlib.util.find_spec(m) is None]; sys.exit(0 if not missing else (print("Missing Python packages: " + ", ".join(missing) + ". Install with: $(PYTHON) -m pip install -r $(ROOT)/requirements.txt", file=sys.stderr) or 2))'

validate: check-deps
	$(PYTHON) -m py_compile $(ROOT)/checklist_guardrails.py $(SCRIPTS)/checklist_validator.py $(SCRIPTS)/draft_case_checklist.py $(SCRIPTS)/run_draft_batch.py $(SCRIPTS)/run_score_batch.py $(SCRIPTS)/score_evidence_with_codex.py $(SCRIPTS)/score_evidence_with_claude.py $(SCRIPTS)/smoke_test.py $(SCRIPTS)/update_case_locks.py
	$(PYTHON) $(SCRIPTS)/smoke_test.py

smoke: check-deps
	$(PYTHON) $(SCRIPTS)/smoke_test.py

draft: check-deps
	@test -n "$(CASE_PACKET)" || { echo 'Missing CASE_PACKET. Usage: make draft CASE_PACKET=/path/to/case_packet.md OUTPUT=/path/to/checklist.yaml'; exit 2; }
	@test -n "$(OUTPUT)" || { echo 'Missing OUTPUT. Usage: make draft CASE_PACKET=/path/to/case_packet.md OUTPUT=/path/to/checklist.yaml'; exit 2; }
	$(PYTHON) $(SCRIPTS)/draft_case_checklist.py \
	  "$(CASE_PACKET)" \
	  $(if $(PROVIDER),--provider "$(PROVIDER)") \
	  $(if $(MODEL),--model "$(MODEL)") \
	  $(if $(REASONING_EFFORT),--reasoning-effort "$(REASONING_EFFORT)") \
	  $(if $(MAX_OUTPUT_TOKENS),--max-output-tokens "$(MAX_OUTPUT_TOKENS)") \
	  $(if $(CODEX_TIMEOUT_SECONDS),--codex-timeout-seconds "$(CODEX_TIMEOUT_SECONDS)") \
	  $(if $(SANDBOX),--codex-sandbox "$(SANDBOX)") \
	  -o "$(OUTPUT)"

draft-codex: PROVIDER = codex
draft-codex: MODEL = gpt-5.4
draft-codex: REASONING_EFFORT = xhigh
draft-codex: CODEX_TIMEOUT_SECONDS = 1800
draft-codex: SANDBOX = read-only
draft-codex: draft

score: check-deps
	@test -n "$(CHECKLIST)" || { echo 'Missing CHECKLIST. Usage: make score CHECKLIST=/path/to/checklist.yaml EVIDENCE_DIR=/path/to/run_artifacts [OUT_PREFIX=/path/to/results/case_score]'; exit 2; }
	@test -n "$(EVIDENCE_DIR)" || { echo 'Missing EVIDENCE_DIR. Usage: make score CHECKLIST=/path/to/checklist.yaml EVIDENCE_DIR=/path/to/run_artifacts [OUT_PREFIX=/path/to/results/case_score]'; exit 2; }
	$(PYTHON) $(SCRIPTS)/score_evidence_with_codex.py \
	  --checklist "$(CHECKLIST)" \
	  --evidence-dir "$(EVIDENCE_DIR)" \
	  $(if $(OUT_PREFIX),--out-prefix "$(OUT_PREFIX)") \
	  $(if $(NATIVE_LABEL_PATH),--native-label-path "$(NATIVE_LABEL_PATH)") \
	  $(if $(MODEL),--model "$(MODEL)") \
	  $(if $(REASONING_EFFORT),--reasoning-effort "$(REASONING_EFFORT)") \
	  $(if $(SANDBOX),--sandbox "$(SANDBOX)") \
	  $(if $(MAX_ATTEMPTS),--max-attempts "$(MAX_ATTEMPTS)")

score-claude: MODEL = sonnet
score-claude: REASONING_EFFORT = high
score-claude: check-deps
	@test -n "$(CHECKLIST)" || { echo 'Missing CHECKLIST. Usage: make score-claude CHECKLIST=/path/to/checklist.yaml EVIDENCE_DIR=/path/to/run_artifacts [OUT_PREFIX=/path/to/results/case_score]'; exit 2; }
	@test -n "$(EVIDENCE_DIR)" || { echo 'Missing EVIDENCE_DIR. Usage: make score-claude CHECKLIST=/path/to/checklist.yaml EVIDENCE_DIR=/path/to/run_artifacts [OUT_PREFIX=/path/to/results/case_score]'; exit 2; }
	$(PYTHON) $(SCRIPTS)/score_evidence_with_claude.py \
	  --checklist "$(CHECKLIST)" \
	  --evidence-dir "$(EVIDENCE_DIR)" \
	  $(if $(OUT_PREFIX),--out-prefix "$(OUT_PREFIX)") \
	  $(if $(NATIVE_LABEL_PATH),--native-label-path "$(NATIVE_LABEL_PATH)") \
	  --model "$(MODEL)" \
	  --reasoning-effort "$(REASONING_EFFORT)" \
	  $(if $(CLAUDE_TIMEOUT_SECONDS),--claude-timeout-seconds "$(CLAUDE_TIMEOUT_SECONDS)") \
	  $(if $(MAX_ATTEMPTS),--max-attempts "$(MAX_ATTEMPTS)")

score-agentdojo-batch: check-deps
	$(PYTHON) $(SCRIPTS)/run_agentdojo_score_batch.py \
	  $(if $(MODEL),--model "$(MODEL)") \
	  $(if $(REASONING_EFFORT),--reasoning-effort "$(REASONING_EFFORT)") \
	  $(if $(SANDBOX),--sandbox "$(SANDBOX)") \
	  $(if $(PER_KEY_CONCURRENCY),--per-key-concurrency "$(PER_KEY_CONCURRENCY)") \
	  $(if $(TASKS_PER_KEY),--tasks-per-key "$(TASKS_PER_KEY)") \
	  $(if $(MAX_ATTEMPTS),--max-attempts "$(MAX_ATTEMPTS)") \
	  $(if $(MAX_RUN_ATTEMPTS),--max-run-attempts "$(MAX_RUN_ATTEMPTS)") \
	  $(if $(FORCE),--force) \
	  $(if $(DRY_RUN),--dry-run)
