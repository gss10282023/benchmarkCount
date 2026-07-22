# Submission-artifact AndroidWorld 100-case manifest verification

## Scope

This check answers only one question: did the frozen anonymous artifact submission already contain a concrete AndroidWorld 100-case list?

It does not audit how the submitted 41 cases were sampled, whether outcomes had already been inspected, or the paper's cost statements.

## Frozen sources

- Anonymous artifact commit: `ffd9ff4e706d85ff2d12e60f087cde664dbae433`
- Ordered 100-case list: `experiments/official_splits/androidworld_full100/androidworld_selected_task_sources.json`
- Ordered-list Git blob: `35b98bf7ffaee1d7ac67caee8a3a5ea591a6303d`
- Ordered-list content SHA-256: `6aa7d2b447742c2333192424941198ca8c8226c29141badfcae09b644a12c320`
- Companion experiment manifest: `experiments/appendix/androidworld_full100_manifest.json`
- Companion-manifest Git blob: `3af08a3d5f638b896c546cb92c16df35366588b3`
- Companion-manifest content SHA-256: `8effc0155e0f900fe41bf11a45f9da0436d7f995132c218d44abb78069689bc1`
- First Git commit on the artifact branch containing both files: `906c2f9863611a36ad75d908923fc53db46a21fa` (`2026-05-07T21:44:37+10:00`)
- Frozen artifact commit time: `2026-05-07T21:50:40+10:00`

## Checks

1. The ordered case list and companion manifest are present in the frozen anonymous artifact commit.
2. The ordered list declares 100 case units and contains exactly 100 entries with ranks 0 through 99. The companion manifest contains the same ordered case IDs.
3. The 100 case IDs are unique.
4. Its recorded case-order hash is `42779d0f49481b02a20f5bf439efca86433ff9dda286ca783780a1d5562c7087`.
5. The submitted AndroidWorld result package contains 41 case directories, and all 41 case IDs occur in the 100-case manifest (`41/41` overlap; no submitted case lies outside it).
6. The ordered list and companion manifest are absent from the separately frozen paper-source commit `35b962c8eb222acbbe4eaf05b9e48859c9d4832e`.

## Evidence boundary

The defensible statement is: **the frozen anonymous artifact submission already contained this exact ordered 100-case AndroidWorld list, and the submitted 41 cases are a subset of it.**

The companion manifest is explicitly marked `status: draft`, `manifest_version: 0.1.0-prelock`, and has no contract locks. Its internal `created_at` value (`2026-05-04T01:54:31+00:00`) is self-reported metadata and is not used by itself to prove an earlier formal freeze. This check also does not establish when the list was chosen relative to observing outcomes.

## Verdict

`PASS`

Step 4B should reuse this exact ordered 100-case list and create a new execution lock before any new run. Runs added after submission must still be reported as post-submission execution.
