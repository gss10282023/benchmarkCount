SHELL := /bin/sh
ROOT_DIR := $(CURDIR)

ifneq ($(wildcard .venv/bin/python),)
PYTHON ?= $(ROOT_DIR)/.venv/bin/python
else ifneq ($(wildcard neurips_ed_track_minimal/.venv/bin/python),)
PYTHON ?= $(ROOT_DIR)/neurips_ed_track_minimal/.venv/bin/python
else
PYTHON ?= python3
endif

.DEFAULT_GOAL := help

.PHONY: help smoke

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make smoke    Run the offline reviewer smoke test' \
	  '' \
	  'Optional override:' \
	  '  make smoke PYTHON=/path/to/python'

smoke:
	$(MAKE) -C neurips_ed_track_minimal smoke PYTHON="$(PYTHON)"
