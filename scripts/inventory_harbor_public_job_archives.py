#!/usr/bin/env python3
"""Inventory authenticated public Harbor job archives without downloading them."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from harbor.auth.constants import SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL
from harbor.auth.tokens import get_access_token


def request_json(url: str, headers: dict[str, str]) -> object:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def head_object(url: str, headers: dict[str, str]) -> dict[str, object]:
    request = urllib.request.Request(url, headers=headers, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return {
                "status": response.status,
                "content_length": int(response.headers.get("Content-Length", "0")),
                "content_type": response.headers.get("Content-Type"),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": exc.code,
            "error": exc.read(1000).decode("utf-8", errors="replace"),
        }


async def build_inventory(job_ids: list[str]) -> dict[str, object]:
    token = await get_access_token()
    headers = {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {token}",
    }
    quoted_ids = ",".join(job_ids)
    query = urllib.parse.urlencode(
        {
            "id": f"in.({quoted_ids})",
            "select": "id,job_name,archive_path,visibility,n_planned_trials,started_at,finished_at",
            "order": "started_at.asc",
        },
        safe="(),",
    )
    rows = request_json(f"{SUPABASE_URL}/rest/v1/job?{query}", headers)
    if not isinstance(rows, list):
        raise RuntimeError("Harbor job query returned a non-list payload")
    by_id = {str(row["id"]): row for row in rows}
    missing = sorted(set(job_ids) - set(by_id))
    if missing:
        raise RuntimeError(f"Harbor did not return requested public jobs: {missing}")

    objects: list[dict[str, object]] = []
    for job_id in job_ids:
        row = by_id[job_id]
        archive_path = str(row["archive_path"])
        object_url = (
            f"{SUPABASE_URL}/storage/v1/object/authenticated/results/"
            f"{urllib.parse.quote(archive_path, safe='/')}"
        )
        objects.append(
            {
                **row,
                "object_url_sha256": hashlib.sha256(object_url.encode()).hexdigest(),
                "head": head_object(object_url, headers),
            }
        )
    total = sum(
        int(item["head"].get("content_length", 0))
        for item in objects
        if isinstance(item.get("head"), dict)
    )
    return {
        "schema_version": "harbor_public_job_archive_inventory/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "job_count": len(objects),
        "known_content_bytes": total,
        "jobs": objects,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("job_ids", nargs="+")
    args = parser.parse_args()
    inventory = asyncio.run(build_inventory(args.job_ids))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n")
    print(json.dumps(inventory, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
