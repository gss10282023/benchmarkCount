# MiniWoB remaining-22 draft VPS bundle

This bundle contains exactly the 22 `miniwob_remaining22` case packets and the
minimal frozen `neurips_ed_track_minimal` draft lifecycle needed to generate
their case checklists. It intentionally contains no benchmark or score launcher.

The launcher uses `gpt-5.6-sol`, reasoning effort `max`, and sets both the regular
and oversized lanes to 11 workers. All 22 packets currently fall into the
oversized lane, so `--large-max-parallel 11` is the setting that provides the
requested 11-way concurrency.

Before extracting on the VPS, verify the archive SHA-256 printed alongside the
local archive. Extract into a fresh directory, then run:

```bash
mkdir miniwob_remaining22_draft_vps_20260718
tar -xzf miniwob_remaining22_draft_vps_20260718.tar.gz \
  -C miniwob_remaining22_draft_vps_20260718
cd miniwob_remaining22_draft_vps_20260718
bash transfer/miniwob_remaining22_draft_vps_20260718/launch_remote.sh
```

Set `PYTHON_BIN` only if the configured VPS Python is not `python3`. Set a fresh
`OUTPUT_ROOT` only when intentionally selecting another isolated result path.
The launcher refuses to mix its ledger with a prior batch.
