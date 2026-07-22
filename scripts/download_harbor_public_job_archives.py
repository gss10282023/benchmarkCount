#!/usr/bin/env python3
"""Stream, verify, and safely extract public Harbor job archives.

The Harbor 0.19 downloader assumes the tarball's root directory exactly matches
the Hub display name. Some leaderboard archives predate that convention. This
tool treats the published tarball as authoritative and extracts it below a
stable job-id directory instead.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harbor.auth.constants import SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL
from harbor.auth.tokens import get_access_token, invalidate_token


CHUNK_BYTES = 8 * 1024 * 1024

TARGET_SELECTORS = {
    "10e2e56b-ed31-5f65-a489-69f78b902adf": {
        "model_name": "openai/gpt-5.5",
        "reasoning_effort": "xhigh",
        "agents": {"codex", "terminus-2"},
    },
    "f9d0318d-30f9-5d6f-bd7f-0ad5acf780d7": {
        "model_name": "anthropic/claude-fable-5",
        "reasoning_effort": "xhigh",
        "agents": {"claude-code"},
    },
    "42cd19c9-42ad-5d79-b033-adf4f879423d": {
        "model_name": "gemini/gemini-3.1-pro-preview",
        "reasoning_effort": "high",
        "agents": {"gemini-cli", "terminus-2"},
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def object_url(archive_path: str) -> str:
    return (
        f"{SUPABASE_URL}/storage/v1/object/authenticated/results/"
        f"{urllib.parse.quote(archive_path, safe='/')}"
    )


def auth_headers(token: str) -> dict[str, str]:
    return {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {token}",
    }


def fresh_token() -> str:
    return asyncio.run(get_access_token())


def stream_download(
    url: str,
    destination: Path,
    expected_bytes: int,
    *,
    retries: int,
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    started = time.monotonic()
    attempts = 0
    reused_existing = False
    if destination.exists():
        if destination.stat().st_size != expected_bytes:
            raise RuntimeError(
                f"Existing archive has unexpected size: {destination.stat().st_size} "
                f"!= {expected_bytes} ({destination})"
            )
        reused_existing = True
    else:
        while (partial.stat().st_size if partial.exists() else 0) < expected_bytes:
            offset = partial.stat().st_size if partial.exists() else 0
            if offset > expected_bytes:
                partial.unlink()
                offset = 0
            headers = auth_headers(fresh_token())
            if offset:
                headers["Range"] = f"bytes={offset}-"
            request = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    if offset and response.status != 206:
                        partial.unlink(missing_ok=True)
                        continue
                    mode = "ab" if offset else "wb"
                    last_report = time.monotonic()
                    with partial.open(mode) as handle:
                        while True:
                            chunk = response.read(CHUNK_BYTES)
                            if not chunk:
                                break
                            handle.write(chunk)
                            if time.monotonic() - last_report >= 15:
                                current = handle.tell()
                                print(
                                    f"GET {destination.name}: {current}/{expected_bytes} bytes",
                                    flush=True,
                                )
                                last_report = time.monotonic()
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                attempts += 1
                status = getattr(exc, "code", None)
                if status in {401, 403}:
                    invalidate_token()
                if attempts > retries:
                    raise RuntimeError(
                        f"Download failed after {attempts} attempts at byte {offset}: {exc}"
                    ) from exc
                time.sleep(min(2**attempts, 30))
                continue

            current = partial.stat().st_size
            if current == expected_bytes:
                break
            attempts += 1
            if current > expected_bytes or attempts > retries:
                raise RuntimeError(
                    f"Unexpected archive size for {destination.name}: "
                    f"{current} != {expected_bytes}"
                )
        os.replace(partial, destination)

    digest = hashlib.sha256()
    with destination.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return {
        "bytes": destination.stat().st_size,
        "sha256": digest.hexdigest(),
        "download_seconds": round(time.monotonic() - started, 3),
        "reused_existing_archive": reused_existing,
    }


def safe_extract(archive: Path, destination: Path) -> dict[str, Any]:
    staging = destination.with_name(destination.name + ".extracting")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        roots = sorted(
            {
                member.name.replace("\\", "/").lstrip("./").split("/", 1)[0]
                for member in members
                if member.name.replace("\\", "/").lstrip("./")
            }
        )
        tar.extractall(staging, filter="data")
    if destination.exists():
        raise FileExistsError(f"Refusing to replace existing directory: {destination}")
    os.replace(staging, destination)

    file_count = 0
    content_bytes = 0
    for path in destination.rglob("*"):
        if path.is_file():
            file_count += 1
            content_bytes += path.stat().st_size
    return {
        "archive_member_count": len(members),
        "archive_roots": roots,
        "extracted_file_count": file_count,
        "extracted_content_bytes": content_bytes,
    }


def _normal_name(member: tarfile.TarInfo) -> str:
    return member.name.replace("\\", "/").lstrip("./")


def _is_core_trial_member(relative_name: str) -> bool:
    if relative_name in {"config.json", "lock.json", "result.json", "trial.log", "exception.txt"}:
        return True
    if relative_name.startswith("verifier/") or relative_name.startswith("artifacts/"):
        return True
    if relative_name.startswith("agent/setup/"):
        return True
    if relative_name.startswith("agent/") and relative_name.count("/") == 1:
        return True
    return False


def _include_selected_member(
    name: str,
    member: tarfile.TarInfo,
    *,
    root_name: str | None,
    selected_prefixes: set[str],
) -> bool:
    if root_name and (
        name == root_name
        or (
            name.startswith(root_name + "/")
            and name.count("/") == 1
            and member.isfile()
        )
    ):
        return True
    name_parts = name.split("/") if name else []
    prefix = "/".join(name_parts[:2]) if len(name_parts) >= 2 else ""
    if prefix not in selected_prefixes:
        return False
    relative_name = name[len(prefix) :].lstrip("/")
    return member.isdir() or _is_core_trial_member(relative_name)


def repack_selected_core(
    source_archive: Path,
    compact_archive: Path,
    *,
    root_name: str | None,
    selected_prefixes: set[str],
) -> dict[str, Any]:
    partial = compact_archive.with_suffix(compact_archive.suffix + ".part")
    partial.unlink(missing_ok=True)
    output_member_count = 0
    output_file_bytes = 0
    try:
        with tarfile.open(source_archive, "r|gz") as source, tarfile.open(
            str(partial), "w|gz", compresslevel=9
        ) as target:
            for member in source:
                name = _normal_name(member)
                if not _include_selected_member(
                    name,
                    member,
                    root_name=root_name,
                    selected_prefixes=selected_prefixes,
                ):
                    continue
                fileobj = source.extractfile(member) if member.isfile() else None
                target.addfile(member, fileobj=fileobj)
                output_member_count += 1
                if member.isfile():
                    output_file_bytes += member.size
                if output_member_count % 1000 == 0:
                    free_bytes = shutil.disk_usage(partial.parent).free
                    if free_bytes < 32 * 1024 * 1024:
                        raise RuntimeError(
                            "Disk fell below 32 MiB while repacking selected core"
                        )
        os.replace(partial, compact_archive)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise

    verify_member_count = 0
    verify_file_bytes = 0
    with tarfile.open(compact_archive, "r|gz") as check:
        for member in check:
            verify_member_count += 1
            if member.isfile():
                verify_file_bytes += member.size
    if (verify_member_count, verify_file_bytes) != (
        output_member_count,
        output_file_bytes,
    ):
        raise RuntimeError("Selected-core compact archive verification failed")
    digest = hashlib.sha256()
    with compact_archive.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return {
        "path": str(compact_archive),
        "bytes": compact_archive.stat().st_size,
        "sha256": digest.hexdigest(),
        "member_count": verify_member_count,
        "file_content_bytes": verify_file_bytes,
    }


def safe_extract_selected_core(
    archive: Path,
    destination: Path,
    selector: dict[str, Any],
) -> dict[str, Any]:
    staging = destination.with_name(destination.name + ".extracting")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    # Pass 1 is streaming: keeping every TarInfo for these large historical
    # jobs can push macOS into several GiB of swap. Only per-trial aggregates
    # and exact selected prefixes are retained in memory.
    roots_set: set[str] = set()
    selected_prefixes: dict[str, dict[str, Any]] = {}
    all_trial_config_count = 0
    archive_member_count = 0
    config_distribution: dict[str, int] = {}
    trajectory_prefixes: set[str] = set()
    prefix_bytes: dict[str, list[int]] = {}
    prefix_counts: dict[str, list[int]] = {}
    with tarfile.open(archive, "r|gz") as tar:
        for member in tar:
            archive_member_count += 1
            name = _normal_name(member)
            if not name:
                continue
            roots_set.add(name.split("/", 1)[0])
            name_parts = name.split("/")
            prefix = "/".join(name_parts[:2]) if len(name_parts) >= 2 else ""
            relative_name = name[len(prefix) :].lstrip("/") if prefix else ""
            if member.isfile() and prefix:
                totals = prefix_bytes.setdefault(prefix, [0, 0])
                counts = prefix_counts.setdefault(prefix, [0, 0])
                if _is_core_trial_member(relative_name):
                    totals[0] += member.size
                    counts[0] += 1
                else:
                    totals[1] += member.size
                    counts[1] += 1
            if relative_name == "agent/trajectory.json" and member.isfile():
                trajectory_prefixes.add(prefix)
            if relative_name != "config.json" or not member.isfile():
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            try:
                data = json.load(extracted)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not (
                isinstance(data, dict)
                and isinstance(data.get("task"), dict)
                and isinstance(data.get("agent"), dict)
                and isinstance(data.get("trial_name"), str)
            ):
                continue
            all_trial_config_count += 1
            agent = data["agent"]
            kwargs = agent.get("kwargs") if isinstance(agent.get("kwargs"), dict) else {}
            key = "|".join(
                [
                    str(agent.get("name")),
                    str(agent.get("model_name")),
                    str(kwargs.get("reasoning_effort")),
                ]
            )
            config_distribution[key] = config_distribution.get(key, 0) + 1
            if (
                agent.get("name") in selector["agents"]
                and agent.get("model_name") == selector["model_name"]
                and kwargs.get("reasoning_effort") == selector["reasoning_effort"]
            ):
                selected_prefixes[prefix] = {
                    "task_name": data["task"].get("name"),
                    "trial_name": data["trial_name"],
                    "agent": agent.get("name"),
                }

    if not selected_prefixes:
        raise RuntimeError(f"No trial configs matched selector {selector}")

    roots = sorted(roots_set)
    root_name = roots[0] if len(roots) == 1 else None
    selected_prefix_set = set(selected_prefixes)
    selected_target_member_bytes = sum(
        prefix_bytes.get(prefix, [0, 0])[0] for prefix in selected_prefixes
    )
    omitted_target_member_bytes = sum(
        prefix_bytes.get(prefix, [0, 0])[1] for prefix in selected_prefixes
    )
    omitted_target_member_count = sum(
        prefix_counts.get(prefix, [0, 0])[1] for prefix in selected_prefixes
    )
    selected_trajectory_count = len(set(selected_prefixes) & trajectory_prefixes)

    free_bytes = shutil.disk_usage(staging.parent).free
    safety_bytes = 32 * 1024 * 1024
    print(
        "SELECT "
        f"{len(selected_prefixes)} trials, "
        f"{selected_trajectory_count} trajectories, "
        f"{selected_target_member_bytes} core bytes, "
        f"{free_bytes} bytes free",
        flush=True,
    )
    compact_record: dict[str, Any] | None = None
    extraction_archive = archive
    if selected_target_member_bytes + safety_bytes > free_bytes:
        compact_archive = archive.with_name(
            archive.name.removesuffix(".tar.gz") + ".selected-core.tar.gz"
        )
        print("REPACK selected core before extraction", flush=True)
        compact_record = repack_selected_core(
            archive,
            compact_archive,
            root_name=root_name,
            selected_prefixes=selected_prefix_set,
        )
        # The compact archive has been independently read back and verified;
        # the original mixed-model download is task-created and recoverable.
        archive.unlink()
        extraction_archive = compact_archive
        free_bytes = shutil.disk_usage(staging.parent).free
        if selected_target_member_bytes + safety_bytes > free_bytes:
            raise RuntimeError(
                "Insufficient disk even after verified selected-core repack: "
                f"need {selected_target_member_bytes + safety_bytes}, have {free_bytes}"
            )

    # Pass 2 streams the archive again and extracts only canonical trajectory,
    # top-level agent log, setup, task/result/lock, artifact, and verifier files.
    extracted_member_count = 0
    with tarfile.open(extraction_archive, "r|gz") as tar:
        for member in tar:
            name = _normal_name(member)
            name_parts = name.split("/") if name else []
            prefix = "/".join(name_parts[:2]) if len(name_parts) >= 2 else ""
            include = _include_selected_member(
                name,
                member,
                root_name=root_name,
                selected_prefixes=selected_prefix_set,
            )
            if include:
                tar.extract(member, path=staging, filter="data")
                extracted_member_count += 1

    if destination.exists():
        raise FileExistsError(f"Refusing to replace existing directory: {destination}")
    os.replace(staging, destination)
    files = [path for path in destination.rglob("*") if path.is_file()]
    return {
        "archive_member_count": archive_member_count,
        "archive_roots": roots,
        "all_trial_config_count": all_trial_config_count,
        "selected_trial_config_count": len(selected_prefixes),
        "selected_task_count": len(
            {str(row["task_name"]) for row in selected_prefixes.values()}
        ),
        "selected_trials_by_agent": dict(
            sorted(
                {
                    agent: sum(row["agent"] == agent for row in selected_prefixes.values())
                    for agent in selector["agents"]
                }.items()
            )
        ),
        "selected_trajectory_member_count": selected_trajectory_count,
        "selected_core_member_bytes": selected_target_member_bytes,
        "omitted_noncore_target_member_count": omitted_target_member_count,
        "omitted_noncore_target_member_bytes": omitted_target_member_bytes,
        "selected_core_repack": compact_record,
        "extraction_archive_path": str(extraction_archive),
        "config_distribution": dict(sorted(config_distribution.items())),
        "extracted_member_count": extracted_member_count,
        "extracted_file_count": len(files),
        "extracted_content_bytes": sum(path.stat().st_size for path in files),
    }


def process_job(
    job: dict[str, Any],
    output_root: Path,
    *,
    retries: int,
    keep_archive: bool,
    selected_only: bool,
) -> dict[str, Any]:
    job_id = str(job["id"])
    archive_path = str(job["archive_path"])
    head = job.get("head") or {}
    expected_bytes = int(head.get("content_length", 0))
    if head.get("status") != 200 or expected_bytes <= 0:
        raise RuntimeError(f"Inventory does not establish archive availability: {job_id}")

    archives_dir = output_root / "raw_archives"
    jobs_dir = output_root / "jobs"
    archive = archives_dir / f"{job_id}.tar.gz"
    destination = jobs_dir / job_id
    record_path = output_root / "manifests" / f"{job_id}.json"

    if destination.exists() and record_path.exists():
        prior = json.loads(record_path.read_text())
        if int(prior.get("archive", {}).get("bytes", -1)) == expected_bytes:
            print(f"SKIP {job_id}: verified extraction record already exists", flush=True)
            return prior
        raise RuntimeError(f"Existing extraction record has wrong archive size: {job_id}")

    download = stream_download(
        object_url(archive_path), archive, expected_bytes, retries=retries
    )
    print(f"EXTRACT {job_id}: {download['bytes']} bytes", flush=True)
    if selected_only:
        selector = TARGET_SELECTORS.get(job_id)
        if selector is None:
            raise RuntimeError(f"No exact target selector registered for {job_id}")
        extraction = safe_extract_selected_core(archive, destination, selector)
    else:
        extraction = safe_extract(archive, destination)
    record = {
        "schema_version": (
            "harbor_public_job_selected_core_extraction/v1"
            if selected_only
            else "harbor_public_job_extraction/v1"
        ),
        "completed_at": utc_now(),
        "job": {
            key: job.get(key)
            for key in (
                "id",
                "job_name",
                "archive_path",
                "visibility",
                "n_planned_trials",
                "started_at",
                "finished_at",
            )
        },
        "archive": {
            **download,
            "remote_etag": head.get("etag"),
            "remote_last_modified": head.get("last_modified"),
            "retained_locally": keep_archive,
        },
        "extraction": extraction,
        "local_job_directory": str(destination),
    }
    write_json(record_path, record)
    if not keep_archive:
        archive.unlink(missing_ok=True)
        compact_path = extraction.get("selected_core_repack", {}).get("path") if isinstance(extraction.get("selected_core_repack"), dict) else None
        if compact_path:
            Path(compact_path).unlink(missing_ok=True)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--job-id", action="append")
    parser.add_argument("--retries", type=int, default=8)
    parser.add_argument("--keep-archives", action="store_true")
    parser.add_argument(
        "--selected-only",
        action="store_true",
        help="Extract only exact target model/effort trials and their core evidence files.",
    )
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text())
    selected = set(args.job_id or [])
    jobs = [
        job
        for job in inventory["jobs"]
        if not selected or str(job["id"]) in selected
    ]
    found = {str(job["id"]) for job in jobs}
    if selected - found:
        raise RuntimeError(f"Requested jobs absent from inventory: {sorted(selected - found)}")

    records = [
        process_job(
            job,
            args.output_root,
            retries=args.retries,
            keep_archive=args.keep_archives,
            selected_only=args.selected_only,
        )
        for job in jobs
    ]
    write_json(
        args.output_root / "download_summary.json",
        {
            "schema_version": "harbor_public_job_download_summary/v1",
            "completed_at": utc_now(),
            "job_count": len(records),
            "archive_bytes": sum(int(record["archive"]["bytes"]) for record in records),
            "extracted_file_count": sum(
                int(record["extraction"]["extracted_file_count"]) for record in records
            ),
            "extracted_content_bytes": sum(
                int(record["extraction"]["extracted_content_bytes"]) for record in records
            ),
            "records": records,
        },
    )


if __name__ == "__main__":
    main()
