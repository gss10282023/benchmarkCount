"""Run or validate the secret-free WebArena OpenRouter credential gate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from evidence_system.core.dotenv import load_project_dotenv
from evidence_system.core.hashing import sha256_file
from evidence_system.webarena_openrouter_credential import (
    CredentialAcceptanceError,
    REQUIRED_MODELS,
    build_openrouter_credential_acceptance,
    validate_openrouter_credential_acceptance_file,
    write_openrouter_credential_acceptance,
)


DEFAULT_OUTPUT = Path(
    "experiments/step20/webarena_verified/openrouter_credential_acceptance.json"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser(
        "probe", help="make exactly three minimal paid model probes"
    )
    probe.add_argument("--dotenv", type=Path, default=Path(".env"))
    probe.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    probe.add_argument("--timeout-seconds", type=int, default=180)
    probe.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    probe.add_argument("--attempt-id", default=None)
    probe.add_argument("--previous-attempt-sha256", default=None)

    validate = subparsers.add_parser(
        "validate", help="validate an existing receipt and its sidecar"
    )
    validate.add_argument("path", type=Path, nargs="?", default=DEFAULT_OUTPUT)

    args = parser.parse_args(argv)
    try:
        if args.command == "probe":
            # This process loads the one private runtime file but never emits its
            # values or value hashes.  The aggregate Step-20 builder never reads it.
            load_project_dotenv(override=True, paths=[args.dotenv])
            api_key = os.environ.get(args.api_key_env, "")
            payload = build_openrouter_credential_acceptance(
                api_key=api_key,
                timeout_seconds=args.timeout_seconds,
                attempt_id=args.attempt_id,
                previous_attempt_sha256=args.previous_attempt_sha256,
            )
            digest = write_openrouter_credential_acceptance(args.output, payload)
            print(
                json.dumps(
                    {
                        "status": payload["status"],
                        "attempt_id": payload["attempt_id"],
                        "previous_attempt_sha256": payload[
                            "previous_attempt_sha256"
                        ],
                        "required_models": list(REQUIRED_MODELS),
                        "model_probe_count": payload["model_probe_count"],
                        "successful_model_probe_count": payload[
                            "successful_model_probe_count"
                        ],
                        "paid_model_probe_count": payload["paid_model_probe_count"],
                        "fallback_model_probe_count": payload[
                            "fallback_model_probe_count"
                        ],
                        "total_cost_credits": payload["total_cost_credits"],
                        "output": str(args.output),
                        "sha256": digest,
                        "credential_material_printed": False,
                        "response_material_printed": False,
                    },
                    ensure_ascii=True,
                    sort_keys=True,
                )
            )
            return 0 if payload["status"] == "pass" else 2
        payload = validate_openrouter_credential_acceptance_file(args.path)
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "path": str(args.path),
                    "sha256": sha256_file(args.path),
                    "credential_material_printed": False,
                    "response_material_printed": False,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 0 if payload["status"] == "pass" else 2
    except CredentialAcceptanceError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "credential_material_printed": False,
                    "response_material_printed": False,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
