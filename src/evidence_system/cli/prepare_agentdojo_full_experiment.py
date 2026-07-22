"""Build the isolated AgentDojo 949-case manifest and immutable definition lock."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_CANDIDATES,
    DEFAULT_CASE_PACKETS,
    DEFAULT_CATALOG,
    DEFAULT_INFRA_CONFIG,
    DEFAULT_LOCK,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_BUNDLE,
    build_experiment_lock,
    build_full_manifest,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paired-candidates", default=str(DEFAULT_CANDIDATES))
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--source-bundle", default=str(DEFAULT_SOURCE_BUNDLE))
    parser.add_argument("--case-packets-root", default=str(DEFAULT_CASE_PACKETS))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--agents-config", default=str(DEFAULT_AGENTS_CONFIG))
    parser.add_argument("--infra-config", default=str(DEFAULT_INFRA_CONFIG))
    parser.add_argument("--created-at")
    parser.add_argument("--locked-at")
    parser.add_argument(
        "--replace-existing-lock-sha256",
        help=(
            "Digest-gated protocol revision: replace a differing existing lock only "
            "when this value exactly matches its current SHA-256."
        ),
    )
    parser.add_argument(
        "--skip-lock",
        action="store_true",
        help="Build only the manifest, before locking runtime code.",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = build_full_manifest(
            catalog_path=args.catalog,
            source_bundle_path=args.source_bundle,
            output_path=args.manifest,
            agents_config_path=args.agents_config,
            infra_config_path=args.infra_config,
            created_at=args.created_at,
        )
        lock = None
        if not args.skip_lock:
            lock = build_experiment_lock(
                candidates_path=args.paired_candidates,
                catalog_path=args.catalog,
                manifest_path=args.manifest,
                source_bundle_path=args.source_bundle,
                case_packets_root=args.case_packets_root,
                output_path=args.lock,
                agents_config_path=args.agents_config,
                infra_config_path=args.infra_config,
                locked_at=args.locked_at,
                replace_existing_lock_sha256=args.replace_existing_lock_sha256,
            )
    except (ContractLifecycleError, ValueError) as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2
    payload = {
        "status": "ok",
        "manifest_path": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "source_bundle_finalized": "0" * 64 not in manifest.read_text(encoding="utf-8"),
        "lock_path": str(lock) if lock is not None else None,
        "lock_sha256": sha256_file(lock) if lock is not None else None,
    }
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
