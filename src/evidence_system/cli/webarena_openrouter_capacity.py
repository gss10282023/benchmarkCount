"""Probe or validate the secret-free WebArena OpenRouter capacity receipt."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from evidence_system.core.dotenv import load_project_dotenv
from evidence_system.webarena_openrouter_capacity import (
    OpenRouterCapacityError,
    build_openrouter_capacity_acceptance,
    validate_openrouter_capacity_acceptance_file,
    write_openrouter_capacity_acceptance,
)


DEFAULT_OUTPUT = Path(
    "experiments/step20/webarena_verified/openrouter_capacity_acceptance.json"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser(
        "probe", help="make exactly one read-only GET of the current-key endpoint"
    )
    probe.add_argument("--dotenv", type=Path, default=Path(".env"))
    probe.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    probe.add_argument("--timeout-seconds", type=int, default=30)
    probe.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    probe.add_argument(
        "--allow-unlimited-key-waiver",
        action="store_true",
        help=(
            "accept a provider-unlimited key while explicitly recording that "
            "account-level remaining credit could not be verified"
        ),
    )

    validate = subparsers.add_parser(
        "validate", help="validate an existing receipt and its sidecar"
    )
    validate.add_argument("path", type=Path, nargs="?", default=DEFAULT_OUTPUT)

    args = parser.parse_args(argv)
    try:
        if args.command == "probe":
            load_project_dotenv(override=True, paths=[args.dotenv])
            api_key = os.environ.get(args.api_key_env, "")
            payload = build_openrouter_capacity_acceptance(
                api_key=api_key,
                timeout_seconds=args.timeout_seconds,
                allow_unlimited_key_waiver=args.allow_unlimited_key_waiver,
            )
            write_openrouter_capacity_acceptance(args.output, payload)
            print(_public_cli_result(payload, path=args.output))
            return 0 if payload["status"] == "pass" else 2

        payload = validate_openrouter_capacity_acceptance_file(args.path)
        print(_public_cli_result(payload, path=args.path))
        return 0 if payload["status"] == "pass" else 2
    except OpenRouterCapacityError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "credential_material_printed": False,
                    "credential_value_hash_printed": False,
                    "authorization_header_printed": False,
                    "response_body_printed": False,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 1


def _public_cli_result(payload: dict[str, object], *, path: Path) -> str:
    return json.dumps(
        {
            "status": payload["status"],
            "http_status": payload["http_status"],
            "provider_limit_mode": payload["provider_limit_mode"],
            "credit_floor_proof_status": payload[
                "credit_floor_proof_status"
            ],
            "output": str(path),
            "credential_material_printed": False,
            "credential_value_hash_printed": False,
            "authorization_header_printed": False,
            "response_body_printed": False,
        },
        ensure_ascii=True,
        sort_keys=True,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
