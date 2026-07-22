PYTHON ?= python3
ROOT := $(abspath ../..)

.PHONY: rebuild test verify

rebuild:
	$(PYTHON) scripts/rebuild_master_table.py \
		--manifest submitted_baseline_manifest.csv \
		--master-out submitted_master_table.csv \
		--summary-out submitted_master_summary.csv \
		--expected-rows 1282

test:
	$(PYTHON) -m unittest discover -s tests -v

verify: rebuild test
	$(PYTHON) -m unittest discover -s ../00_submission_repo_lock/tests -v
	$(PYTHON) scripts/verify_step1.py \
		--root $(ROOT) \
		--report verification_report.json
	(cd ../00_submission_repo_lock && shasum -a 256 -c SHA256SUMS)
	shasum -a 256 -c SHA256SUMS
