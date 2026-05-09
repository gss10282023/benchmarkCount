# Other VPS Snapshot

Source host:
`other-vps-01` (`134.199.161.171`, hostname `ubuntu-s-8vcpu-16gb-amd-syd1`)

Purpose:
This snapshot preserves the machine-specific runtime state needed to rebuild the second VPS while excluding `.env`, secrets, and oversized environment packaging.

Included in this branch:
- `system/summary.txt`: OS, kernel, CPU, memory, disk, Docker version, running containers.
- `system/benchmarks.txt`: benchmark repo revisions found on the VPS.
- `system/project_tree_top.txt`: top-level project layout under `/root/revised_agent_benchmark_paper_package`.
- `system/root_tree_top.tsv`: top-level `/root` layout snapshot.
- `system/results_full_manifest.tsv.gz`: full file manifest for `/root/revised_agent_benchmark_paper_package/results/full`.
- `system/results_full_top200.tsv`: largest files inside that `results/full` tree.
- `project/root_docs/`: machine-local project docs copied from the VPS, including `.workarena_instances_pool_v2_no16.json`, `README_PACKAGE.md`, `实验说明.md`, `计划.md`.
- `project/results/`: preserved `smoke`, `logs`, `failures`, `preflight`, `raw`, and `rerun` artifacts.
- `project/tmp/`: preserved tmp/browser artifact state from the VPS.
- `project/.appworld/`: AppWorld local runtime directory from the VPS.
- `data/base_dbs/`: AppWorld base databases.
- `data/tasks/`: AppWorld task definitions copied from `/root/data/tasks`.
- `data/version.txt` and `data/README_BEFORE_SHARING.md`.

Intentionally excluded:
- `.env`, secrets, SSH material, virtualenvs, caches.
- `/root/revised_agent_benchmark_paper_package/results/full` payload files.
The VPS had about `692M` of `results/full`; this branch stores a manifest instead of duplicating the payload.

Sanitization:
- AppWorld smoke logs and task files were copied, then locally redacted for `api_key`, `Authorization: Bearer`, and long access-token values before commit.
- The snapshot is intended to remain re-uploadable to a rebuilt VPS without carrying live credentials.

Known benchmark revisions on the VPS:
- `benchmarks/tau2-bench`: `2be691669909439cf88dedc13decf94b7664d262`
- `benchmarks/appworld-official-a072b7a`: `a072b7a86e7c1d5b1d7175659d750ebb9b79f10a`
- `benchmarks/agentdojo`, `benchmarks/workarena`, `benchmarks/appworld`: present as runtime directories but not Git clones.

Observed runtime stack:
- Ubuntu `24.04.3 LTS`
- Docker `29.1.3`
- No long-running containers were active at snapshot time.

Rebuild outline:
1. Provision an Ubuntu 24.04 VPS with roughly 8 vCPU, 16 GiB RAM, and at least 300 GiB disk.
2. Clone this repository branch onto the new machine.
3. Restore `vps_snapshots/other-vps-01/data/` to `/root/data/` if you want the same AppWorld databases and task files available immediately.
4. Restore `vps_snapshots/other-vps-01/project/.appworld/` to `/root/.appworld/`.
5. Restore `vps_snapshots/other-vps-01/project/results/` and `vps_snapshots/other-vps-01/project/tmp/` back into `/root/revised_agent_benchmark_paper_package/` if you want the preserved runtime traces and browser artifacts.
6. Re-clone or reinstall the benchmark runtimes under `/root/benchmarks/`, using the revisions in `system/benchmarks.txt` where Git history was available.
7. Recreate `.env` manually and reinstall Python/system dependencies separately; those were intentionally not committed here.
8. Use `system/results_full_manifest.tsv.gz` when you need to repopulate selected full-run artifacts from external storage.

Notes:
- The project directory on the VPS was not a Git clone; it was a runtime copy under `/root/revised_agent_benchmark_paper_package`.
- The `data/base_dbs/*.db` files are stored in Git LFS on this branch to avoid large normal Git blobs.
