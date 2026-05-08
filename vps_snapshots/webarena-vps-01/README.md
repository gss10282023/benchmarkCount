# WebArena VPS Snapshot

Source host:
`webarena-vps-01` (`45.76.116.86`, hostname `vultr`)

Purpose:
This snapshot preserves the machine-specific state needed to rebuild the WebArena VPS without committing the very large environment tarballs or secrets.

Included in this branch:
- `system/summary.txt`: OS, kernel, CPU, memory, disk, Docker version, running containers.
- `system/benchmarks.txt`: benchmark repo revisions found on the VPS.
- `system/project_tree_top.txt`: top-level project layout under `/root/revised_agent_benchmark_paper_package`.
- `system/root_tree_top.tsv`: top-level `/root` layout snapshot.
- `system/results_full_manifest.tsv.gz`: full file manifest for `/root/revised_agent_benchmark_paper_package/results/full`.
- `system/results_full_top200.tsv`: largest files inside that `results/full` tree.
- `root/bootstrap.sh`: host bootstrap script.
- `root/db_download.log`: database/bootstrap note from the machine.
- `root/logs/`: root-level log directory from the machine.
- `project/results/smoke/`: smoke run artifacts copied from the VPS.

Intentionally excluded:
- `.env`, secrets, SSH material, virtualenvs, caches.
- `/root/nominatim_volumes.tar.C8C8bef3` and `/root/osm_tile_server.tar.e4Ca254f`.
- `/root/revised_agent_benchmark_paper_package/results/full` payload files.
The full-results tree is represented here by manifests only, because the branch base already contains repo-level `results/full` data and the VPS-local tree would otherwise duplicate another `1.1G`.

Known benchmark revisions on the VPS:
- `benchmarks/webarena`: `dce04686a56253aefba7b18a4fa0937cf1dc987b`
- `benchmarks/miniwob-plusplus`: `7fd85d71a4b60325c6585396ec4f48377d049838`

Observed runtime stack:
- Ubuntu `24.04.4 LTS`
- Docker `29.1.3`
- Running containers at snapshot time included `wikipedia`, `forum`, `gitlab`, `map`, `map-db`, `shopping`, `shopping_admin`

Rebuild outline:
1. Provision an Ubuntu 24.04 VPS with roughly 8 vCPU, 64 GiB RAM, and at least 750 GiB disk.
2. Clone this repository branch onto the new machine.
3. Restore `vps_snapshots/webarena-vps-01/root/bootstrap.sh` and `vps_snapshots/webarena-vps-01/root/db_download.log` to `/root/` if you want the same operator notes and bootstrap entrypoint.
4. Re-clone benchmark repos under `/root/benchmarks/` and check out the revisions listed above.
5. Restore `vps_snapshots/webarena-vps-01/project/results/smoke/` back to `/root/revised_agent_benchmark_paper_package/results/smoke/` if you want the preserved smoke artifacts on the rebuilt host.
6. Use `system/results_full_manifest.tsv.gz` and `system/results_full_top200.tsv` to decide which full-run artifacts need to be copied back from external storage.
7. Recreate the large map/database assets outside Git, then bring up the containers recorded in `system/summary.txt`.

Notes:
- The project directory on the VPS was not a Git clone; it was a runtime copy under `/root/revised_agent_benchmark_paper_package`.
- This snapshot is meant to preserve machine state, not to replace the large external datasets required by the WebArena stack.
