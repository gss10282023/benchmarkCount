PYTHON ?= python3
ROOT := $(abspath ../..)
HERE := $(abspath .)

.PHONY: rebuild test verify checksums clean-python-cache

rebuild:
	$(PYTHON) scripts/build_reconstruction.py --repo-root $(ROOT) --output-dir $(HERE)

test: rebuild
	$(PYTHON) -m unittest discover -s tests -v

verify: test
	$(PYTHON) scripts/verify_step2.py \
		--repo-root $(ROOT) \
		--output-dir $(HERE) \
		--report $(HERE)/verification_report.json \
		--status $(HERE)/STATUS.json
	$(PYTHON) scripts/write_sha256s.py $(HERE)
	shasum -a 256 -c SHA256SUMS

checksums:
	$(PYTHON) scripts/write_sha256s.py $(HERE)

clean-python-cache:
	find scripts tests -type d -name __pycache__ -prune -exec rm -rf {} +
