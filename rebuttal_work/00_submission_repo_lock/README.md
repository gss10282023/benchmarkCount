# Step 1 repository lock

This directory separates the submitted artifact execution snapshot from the later working repository.

- `SUBMISSION_REPO` is a read-only sparse worktree at `ffd9ff4e706d85ff2d12e60f087cde664dbae433`, the last locally evidenced push to `origin/neurips-ed-code-release`. It materializes the minimal code, frozen selectors, and every decisive file referenced by the 1,282-row baseline.
- The final paper source is locked separately at `35b962c8eb222acbbe4eaf05b9e48859c9d4832e`; it is not conflated with the artifact execution commit.
- The actual later workspace is the `LEGACY_MODIFIED_REPO`. It is dirty and is not claimed clean. `repo_diff_index.json` records its tracked/untracked top-level state, and the Step 1 builders reject it as a membership or numeric source. Its scientific-input roots `neurips_ed_track_minimal/`, `results/`, and `paper_result_packages/` are recursively protected by macOS `UF_IMMUTABLE` (`uchg`); the acceptance verifier checks every entry. `LEGACY_HEAD_SNAPSHOT` is only a clean, read-only reference for its HEAD commit.
- New execution output is confined to `rebuttal_work/runtime_outputs/submission_rebuttal`, outside both locked snapshots and the old `results/` tree.

There is no immutable submission tag or OpenReview-attached archive hash available locally. The selection basis and this qualification are recorded in `submission_repo_lock.json`. The complete deterministic Git archive stream hashes to `6fc564e106ba92317c931427cdab759070296857e3d1a22347bbb682ac156ea5`; the materialized 550 KiB tar is explicitly scoped only to `neurips_ed_track_minimal`.

Regenerate the lock metadata with:

```bash
python3 scripts/build_repo_lock.py --root ../.. --output-dir .
```

The full acceptance command is documented in `../01_submission_baseline/README.md`.

Operational note: later work must write only under `rebuttal_work/runtime_outputs/submission_rebuttal`. If an authorized future step must deliberately unlock the legacy roots, the reversible command is `chflags -R nouchg neurips_ed_track_minimal results paper_result_packages`; doing so invalidates Step 1 acceptance until the roots are locked and verified again.
