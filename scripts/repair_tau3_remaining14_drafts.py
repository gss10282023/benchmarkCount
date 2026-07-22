#!/usr/bin/env python3
"""Repair the canonical Tau3 remaining-14 checklist drafts without rewriting model attempts.

The generated ``attempt_*`` artifacts remain immutable provenance.  This script only
updates the canonical ``checklist.json`` / ``checklist.yaml`` pair and writes a receipt
that identifies the generated attempt from which each reviewed revision was derived.
All semantic additions are grounded in the outcome-free case packets.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
JOB_ROOT = REPO_ROOT / "transfer" / "tau3_remaining14_redraft_vps_20260719"
RESULTS_ROOT = JOB_ROOT / "results"
PACKETS_ROOT = JOB_ROOT / "case_packets"
CASE_IDS = ("4", "9", "24", "42", "43", "44", "48", "55", "63", "85", "88", "96", "104", "110")

EVALUATOR = "official/tau2_bench/src/tau2/evaluator/evaluator.py::evaluate_simulation"
ENV_EVALUATOR = (
    "official/tau2_bench/src/tau2/evaluator/"
    "evaluator_env.py::EnvironmentEvaluator.calculate_reward"
)
NL_EVALUATOR = (
    "official/tau2_bench/src/tau2/evaluator/"
    "evaluator_nl_assertions.py::NLAssertionsEvaluator.calculate_reward"
)
ARTIFACT_COMPONENT_SUPPORT = [
    "derived/artifact_inventory.json::artifact_classes[0].path_pattern",
    "derived/artifact_inventory.json::artifact_classes[0].container_path",
    "derived/artifact_inventory.json::artifact_classes[0].selection_rule",
    "derived/artifact_inventory.json::artifact_classes[0].field_paths",
    "derived/artifact_inventory.json::artifact_classes[0].serialized_values",
    "derived/artifact_inventory.json::artifact_classes[0].contents[1]",
    "derived/artifact_inventory.json::artifact_classes[0].contents[2]",
    "derived/artifact_inventory.json::artifact_classes[0].contents[3]",
    "derived/artifact_inventory.json::artifact_classes[0].contents[6]",
    "derived/artifact_inventory.json::artifact_classes[0].limitations[0]",
    "derived/task.json::evaluation_criteria.reward_basis",
    "derived/task.json::evaluation_criteria.nl_assertions",
    EVALUATOR,
    ENV_EVALUATOR,
    NL_EVALUATOR,
]
TOOL_LOG_SUPPORT = [
    "derived/artifact_inventory.json::artifact_classes[2].path_pattern",
    "derived/artifact_inventory.json::artifact_classes[2].contents[0]",
    "derived/artifact_inventory.json::artifact_classes[2].contents[1]",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    result = subprocess.run(
        [
            "ruby",
            "-rjson",
            "-ryaml",
            "-e",
            "obj=JSON.parse(STDIN.read); print YAML.dump(obj).sub(/\\A---\\s*\\n/, '')",
        ],
        input=json.dumps(value, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=True,
    )
    path.write_text(result.stdout, encoding="utf-8")


def load_yaml_as_json(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ruby",
            "-rjson",
            "-ryaml",
            "-e",
            "print JSON.generate(YAML.safe_load(STDIN.read, aliases: false))",
        ],
        input=path.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=True,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML object: {path}")
    return value


def generated_source_attempt(
    case_dir: Path,
    canonical: dict[str, Any],
    existing_case_receipt: dict[str, Any] | None,
) -> tuple[str, str]:
    matches: list[tuple[str, str]] = []
    for path in sorted(case_dir.glob("attempt_*.checklist.json")):
        if load_json(path) == canonical:
            matches.append((path.name, sha256_file(path)))
    if len(matches) == 1:
        return matches[0]
    if not matches and existing_case_receipt is not None:
        name = str(existing_case_receipt["source_generated_attempt"])
        expected_sha256 = str(existing_case_receipt["source_generated_attempt_sha256"])
        source_path = case_dir / name
        if source_path.is_file() and sha256_file(source_path) == expected_sha256:
            return name, expected_sha256
    raise ValueError(
        f"Canonical checklist must match exactly one generated attempt before first repair, "
        f"or have a valid existing receipt: {case_dir} matches={matches}"
    )


def task_nl_assertion_count(case_id: str) -> int:
    task = load_json(PACKETS_ROOT / case_id / "raw_case" / "derived" / "task.json")
    criteria = task.get("evaluation_criteria") or {}
    return len(criteria.get("nl_assertions") or [])


def replace_enum_names(node: Any) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                node[key] = value.replace("AGENT_STOP", "agent_stop").replace(
                    "USER_STOP", "user_stop"
                )
            else:
                replace_enum_names(value)
    elif isinstance(node, list):
        for value in node:
            replace_enum_names(value)


def repair_native_artifact_rules(
    checklist: dict[str, Any], *, nl_assertion_count: int
) -> None:
    native = checklist["native"]
    replace_enum_names(native)
    has_nl = nl_assertion_count > 0

    nl_definition = (
        f"the {nl_assertion_count} official NL assertion(s) are each matched to one "
        "retained per-assertion judgment and every matched judgment has `met=true`"
        if has_nl
        else "the official task has an empty NL-assertion set, so the NL_ASSERTION "
        "component is satisfied vacuously"
    )
    native["benchmark_success"] = {
        "text": (
            "The released native criterion is the conjunction of: (1) normal termination "
            "with `termination_reason` equal to `agent_stop` or `user_stop`; (2) the DB "
            "component produced by the official complete predicted-agent/user DB comparison "
            "matches the gold environment obtained by replaying the official action list; "
            f"and (3) {nl_definition}. This defines the native claim but does not make the "
            "released scalar reward or released success/fail label evidence for the later "
            "independent S/F/U judgment."
        ),
        "support": [
            "derived/task.json::evaluation_criteria.reward_basis",
            "derived/task.json::evaluation_criteria.actions",
            "derived/task.json::evaluation_criteria.nl_assertions",
            EVALUATOR,
            ENV_EVALUATOR,
            NL_EVALUATOR,
            "derived/artifact_inventory.json::native_db_evidence_rule",
            "derived/artifact_inventory.json::artifact_classes[0].limitations[0]",
        ],
    }

    native["checked_by"] = {
        "text": (
            "Independently inspect component evidence in `adapter/native_run/results.json`: "
            "select the unique `simulations[*]` entry whose `task_id` matches this case; "
            "read `termination_reason` from that entry, and read `db_check.db_match`, "
            "`db_check.db_reward`, and (when the locked task has NL assertions) the "
            "case-matched `nl_assertions[*].nl_assertion` and `.met` fields from nested "
            "`reward_info`. Do not use `reward_info.reward`, runtime `reward_basis`, "
            "`reward_breakdown`, any prior score, or the separately retained released "
            "success/fail label to choose S, F, or U."
        ),
        "support": list(ARTIFACT_COMPONENT_SUPPORT),
    }

    native["decisive_artifacts"] = [
        {
            "artifact": (
                "adapter/native_run/results.json "
                "(the simulations[*] entry whose task_id matches this case)"
            ),
            "question": (
                "Without consulting the released scalar reward or label, do the "
                "case-matched termination, DB-comparison, and applicable per-assertion NL "
                "component fields establish every element of the locked native criterion?"
            ),
            "support": list(ARTIFACT_COMPONENT_SUPPORT),
        }
    ]
    nl_success = (
        f"the retained NL judgments cover each of the {nl_assertion_count} locked "
        "official assertion(s) exactly once and every matched judgment has `met=true`"
        if has_nl
        else "the locked official task source contains no NL assertions, so no per-record "
        "scalar or reward-breakdown field is required for that vacuous component"
    )
    native["success_if"] = [
        {
            "text": (
                "In `adapter/native_run/results.json`, the `simulations[*]` entry whose "
                "`task_id` matches this case has `termination_reason` in "
                "{`agent_stop`, `user_stop`}; its `reward_info.db_check` has "
                "`db_match=true` and `db_reward=1.0`; and "
                f"{nl_success}."
            ),
            "support": list(ARTIFACT_COMPONENT_SUPPORT),
        }
    ]
    native["fail_if"] = [
        {
            "text": (
                "The case-matching `simulations[*]` entry records `termination_reason` "
                "outside {`agent_stop`, `user_stop`}. This component establishes native "
                "failure directly; the released scalar reward or label is not consulted."
            ),
            "support": [
                "derived/artifact_inventory.json::artifact_classes[0].path_pattern",
                "derived/artifact_inventory.json::artifact_classes[0].container_path",
                "derived/artifact_inventory.json::artifact_classes[0].selection_rule",
                "derived/artifact_inventory.json::artifact_classes[0].field_paths",
                "derived/artifact_inventory.json::artifact_classes[0].serialized_values",
                "derived/artifact_inventory.json::artifact_classes[0].contents[6]",
                EVALUATOR,
            ],
        },
        {
            "text": (
                "The case-matching simulation's `reward_info.db_check` consistently records "
                "`db_match=false` and `db_reward=0.0`. Because DB is in the locked native "
                "criterion, this component evidence establishes native failure without "
                "using the released scalar reward or label."
            ),
            "support": [
                "derived/artifact_inventory.json::artifact_classes[0].path_pattern",
                "derived/artifact_inventory.json::artifact_classes[0].selection_rule",
                "derived/artifact_inventory.json::artifact_classes[0].field_paths",
                "derived/artifact_inventory.json::artifact_classes[0].contents[1]",
                "derived/artifact_inventory.json::artifact_classes[0].contents[2]",
                "derived/task.json::evaluation_criteria.reward_basis",
                EVALUATOR,
                ENV_EVALUATOR,
            ],
        },
    ]
    if has_nl:
        native["fail_if"].append(
            {
                "text": (
                    "With allowed termination, the case-matching simulation's "
                    "`reward_info.nl_assertions` contains a judgment matched to one of the "
                    "locked official assertions with `met=false`; because NL_ASSERTION is "
                    "in the locked native criterion, that component evidence establishes "
                    "native failure without using the released scalar reward or label."
                ),
                "support": [
                    "derived/artifact_inventory.json::artifact_classes[0].path_pattern",
                    "derived/artifact_inventory.json::artifact_classes[0].selection_rule",
                    "derived/artifact_inventory.json::artifact_classes[0].field_paths",
                    "derived/artifact_inventory.json::artifact_classes[0].contents[1]",
                    "derived/artifact_inventory.json::artifact_classes[0].contents[3]",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    "derived/task.json::evaluation_criteria.nl_assertions",
                    EVALUATOR,
                    NL_EVALUATOR,
                ],
            }
        )
    native["undecided_if"] = [
        {
            "text": (
                "The case-matching `simulations[*]` entry cannot be identified, or the "
                "retained component evidence is missing, truncated, misassociated, or "
                "internally inconsistent (including disagreement between `db_match` and "
                "`db_reward`, or incomplete/duplicate/mismatched NL judgments where NL "
                "assertions are required), so neither native success nor native failure is "
                "established. Missing `reward_info.reward`, runtime `reward_basis`, "
                "`reward_breakdown`, a prior score, or the released label alone never "
                "causes U because those values are non-decisive. Conversation, tool logs, "
                "or partial entity views alone do not establish the official complete "
                "agent/user DB comparison."
            ),
            "support": [
                "derived/artifact_inventory.json::artifact_classes[0].path_pattern",
                "derived/artifact_inventory.json::artifact_classes[0].container_path",
                "derived/artifact_inventory.json::artifact_classes[0].selection_rule",
                "derived/artifact_inventory.json::artifact_classes[0].field_paths",
                "derived/artifact_inventory.json::artifact_classes[0].serialized_values",
                "derived/artifact_inventory.json::artifact_classes[0].contents[0]",
                "derived/artifact_inventory.json::artifact_classes[0].contents[1]",
                "derived/artifact_inventory.json::artifact_classes[0].contents[2]",
                "derived/artifact_inventory.json::artifact_classes[0].contents[3]",
                "derived/artifact_inventory.json::artifact_classes[0].contents[6]",
                "derived/artifact_inventory.json::artifact_classes[2].limitations[0]",
                "derived/artifact_inventory.json::native_db_evidence_rule",
            ],
        }
    ]


def condition(
    *,
    condition_id: str,
    text: str,
    rationale: str,
    question: str,
    support: list[str],
) -> dict[str, Any]:
    return {
        "id": condition_id,
        "text": text,
        "rationale": rationale,
        "decisive_artifacts": [
            {
                "artifact": (
                    "adapter/native_run/artifacts/task_<task_id>/"
                    "sim_<simulation_id>/task.log"
                ),
                "question": question,
                "support": list(TOOL_LOG_SUPPORT) + support,
            }
        ],
        "support": support,
    }


def upsert_condition(checklist: dict[str, Any], value: dict[str, Any]) -> None:
    conditions = checklist["stronger"]["additional_conditions"]
    for index, current in enumerate(conditions):
        if current.get("id") == value["id"]:
            conditions[index] = value
            return
    conditions.append(value)


def workflow_condition(
    *,
    condition_id: str,
    text: str,
    question: str,
    policy_support: list[str],
) -> dict[str, Any]:
    return condition(
        condition_id=condition_id,
        text=text,
        rationale=(
            "These are concrete prerequisites stated by this case's official user "
            "scenario and the released retail policy, but the locked DB + NL_ASSERTION "
            "native criterion does not operationalize the authentication, state-check, "
            "confirmation, item-completeness, or payment-selection workflow itself."
        ),
        question=question,
        support=[
            "derived/task.json::user_scenario.instructions.known_info",
            "derived/task.json::user_scenario.instructions.unknown_info",
            "derived/task.json::user_scenario.instructions.reason_for_call",
            *policy_support,
            "derived/task.json::evaluation_criteria.reward_basis",
            EVALUATOR,
        ],
    )


def repair_case_specific(case_id: str, checklist: dict[str, Any]) -> list[str]:
    revisions: list[str] = []
    if case_id == "4":
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="explicit_confirmation_before_modifications",
                text=(
                    "Beyond native success, before each pending-order item modification "
                    "the retained record shows that the agent checked the order was "
                    "pending, collected the complete set of t-shirts to change for that "
                    "order, reminded the user to confirm all requested items were included, "
                    "listed the purple/size-S/v-neck/material choices and payment method "
                    "for any price difference, and obtained an explicit user `yes`."
                ),
                question=(
                    "For every item-modification call, do the preceding records establish "
                    "pending status, the complete per-order item set, the requested options, "
                    "a user-provided or authorized payment method, and explicit yes?"
                ),
                policy_support=[
                    "official/policy.md::lines 16-16",
                    "official/policy.md::lines 82-84",
                    "official/policy.md::lines 94-98",
                    "official/policy.md::lines 108-114",
                ],
            ),
        )
        revisions.append(
            "strengthened pending-status, complete-item-set, payment, and confirmation checks"
        )

    if case_id == "9":
        checklist["native"]["user_goal"] = {
            "text": (
                "Help Mei Kovacs with a delivered-order exchange: she initially wants to "
                "exchange the water bottle and desk lamp, preferring the brighter desk-lamp "
                "power options in the order AC adapter, battery, then USB, but at "
                "confirmation she changes her mind and authorizes only the desk-lamp exchange."
            ),
            "support": [
                "derived/task.json::user_scenario.instructions.known_info",
                "derived/task.json::user_scenario.instructions.reason_for_call",
            ],
        }
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="policy_auth_and_revised_confirmation",
                text=(
                    "Beyond native success, the retained record shows name-plus-zip "
                    "authentication before user-specific help, verifies the order was "
                    "delivered, treats the user's retraction as replacing the original "
                    "two-item request, reminds the user to confirm the complete revised "
                    "exchange set, lists only the desk lamp and selected brighter variant "
                    "plus a user-provided or authorized payment method, and obtains explicit "
                    "`yes` before the exchange call."
                ),
                question=(
                    "Does the record establish name-plus-zip authentication, delivered "
                    "status, complete revised one-item scope, payment authorization, and "
                    "explicit yes before exchanging only the desk lamp?"
                ),
                policy_support=[
                    "official/policy.md::lines 10-16",
                    "official/policy.md::lines 82-84",
                    "official/policy.md::lines 128-136",
                ],
            ),
        )
        revisions.extend(
            [
                "restored the task-backed desk-lamp power preference in native.user_goal",
                "strengthened delivered-status, revised-item-set, payment, and confirmation checks",
            ]
        )

    if case_id == "24":
        upsert_condition(
            checklist,
            condition(
                condition_id="no_order_update_after_retraction",
                text=(
                    "Beyond native success, retained tool records show no cancellation or "
                    "other order-update call was made without the policy-required explicit "
                    "confirmation at any point, and no such call occurred after Sofia "
                    "retracted the grill-cancellation request and chose to keep it."
                ),
                rationale=(
                    "The official scenario makes the retraction decisive and the policy "
                    "requires explicit confirmation before every database update. The "
                    "native DB + NL_ASSERTION criterion does not score attempted or "
                    "non-persistent update calls as a workflow condition."
                ),
                question=(
                    "Do the tool and conversation records contain no unconfirmed order "
                    "update before retraction and no cancellation/update call after retraction?"
                ),
                support=[
                    "derived/task.json::user_scenario.instructions.reason_for_call",
                    "official/policy.md::lines 16-16",
                    "official/policy.md::lines 86-92",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    EVALUATOR,
                ],
            ),
        )
        upsert_condition(
            checklist,
            condition(
                condition_id="authenticate_before_order_disclosure",
                text=(
                    "Beyond native success, the retained conversation/tool record shows "
                    "that the agent authenticated Sofia Hernandez by name plus zip before "
                    "looking up or disclosing her order and product information."
                ),
                rationale=(
                    "The retail policy requires authentication before user-specific order, "
                    "product, or profile assistance, while this case's native DB plus "
                    "NL_ASSERTION reward does not score authentication."
                ),
                question=(
                    "Does the record show name-plus-zip authentication before any lookup "
                    "or disclosure of Sofia Hernandez's orders and t-shirt details?"
                ),
                support=[
                    "derived/task.json::user_scenario.instructions.known_info",
                    "derived/task.json::user_scenario.instructions.unknown_info",
                    "official/policy.md::lines 10-12",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    EVALUATOR,
                ],
            ),
        )
        revisions.extend(
            [
                "broadened the retraction guard to all unconfirmed order updates",
                "added policy-backed authentication stronger condition",
            ]
        )

    if case_id == "42":
        upsert_condition(
            checklist,
            condition(
                condition_id="verify_state_before_conditional_updates",
                text=(
                    "Beyond native success, the retained record shows that the agent first "
                    "checked the current user and order addresses and checked the jigsaw "
                    "order/status and product variants; it corrected only the mismatching "
                    "addresses and changed the jigsaw only while the order was pending, "
                    "selecting an available easiest-level, least-pieces variant."
                ),
                rationale=(
                    "The official scenario makes the address corrections and jigsaw change "
                    "conditional on facts the agent must check. The native DB hash can match "
                    "the final state without proving those case-specific checks because "
                    "ACTION and COMMUNICATE are outside this task's reward basis."
                ),
                question=(
                    "Do the conversation and tool records show the required address, order-"
                    "status, and product checks before the conditional updates?"
                ),
                support=[
                    "derived/task.json::user_scenario.instructions.reason_for_call",
                    "derived/task.json::evaluation_criteria.actions[1]",
                    "derived/task.json::evaluation_criteria.actions[2]",
                    "derived/task.json::evaluation_criteria.actions[3]",
                    "derived/task.json::evaluation_criteria.actions[7]",
                    "derived/task.json::evaluation_criteria.actions[8]",
                    "official/policy.md::Modify pending order",
                    "official/policy.md::Modify items",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    EVALUATOR,
                ],
            ),
        )
        revisions.append("added task-backed conditional verification stronger condition")

    if case_id == "43":
        checklist["native"]["user_goal"] = {
            "text": (
                "Tell Lucas Santos the shipped-to address, tracking number, and whether the "
                "order is still in transit; tell him the tablet storage; and change his "
                "default address to his daughter's Chicago address."
            ),
            "support": ["derived/task.json::user_scenario.instructions.reason_for_call"],
        }
        upsert_condition(
            checklist,
            condition(
                condition_id="authenticate_before_order_disclosure_or_update",
                text=(
                    "Beyond native success, the retained record shows that the agent "
                    "authenticated Lucas Santos by name plus zip before looking up or "
                    "disclosing order/profile information and before changing his default "
                    "address."
                ),
                rationale=(
                    "The retail policy requires authentication before user-specific "
                    "assistance, but this case's released DB plus NL_ASSERTION reward does "
                    "not score that prerequisite."
                ),
                question=(
                    "Does the record show name-plus-zip authentication before the first "
                    "user-specific order/profile lookup, disclosure, or update?"
                ),
                support=[
                    "derived/task.json::user_scenario.instructions.known_info",
                    "derived/task.json::user_scenario.instructions.unknown_info",
                    "official/policy.md::lines 10-12",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    EVALUATOR,
                ],
            ),
        )
        revisions.extend(
            [
                "removed policy authentication from native.user_goal",
                "added policy-backed authentication stronger condition",
            ]
        )

    if case_id == "44":
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="auth_before_assistance",
                text=(
                    "Beyond native success, the retained record shows that Aarav Anderson, "
                    "who does not remember his email, was authenticated by name plus zip "
                    "before any order/product disclosure or modification."
                ),
                question=(
                    "Was Aarav authenticated by name plus zip before the first "
                    "user-specific lookup, disclosure, or update?"
                ),
                policy_support=["official/policy.md::lines 10-16"],
            ),
        )
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="confirm_before_modify",
                text=(
                    "Beyond native success, the retained record shows the order was checked "
                    "as pending; the complete single-call item change, cheapest available "
                    "desk-lamp variant, and task-authorized gift-card price-difference method "
                    "were listed; the user was reminded to confirm the complete item set; "
                    "and explicit `yes` was obtained before modification."
                ),
                question=(
                    "Before modification, do the records establish pending status, the "
                    "complete item/change details, gift-card handling, the completeness "
                    "reminder, and explicit yes?"
                ),
                policy_support=[
                    "official/policy.md::lines 16-16",
                    "official/policy.md::lines 82-84",
                    "official/policy.md::lines 94-98",
                    "official/policy.md::lines 108-114",
                ],
            ),
        )
        revisions.append(
            "corrected authentication route and strengthened pending/item-completeness confirmation checks"
        )

    if case_id == "48":
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="authenticate_and_confirm_before_return",
                text=(
                    "Beyond native success, the retained record shows Daiki Johnson, who "
                    "does not remember his email, was authenticated by name plus zip; the "
                    "air-purifier order was checked as delivered; the order, returned item, "
                    "and task-specified original refund method were listed; and explicit "
                    "`yes` was obtained before the return call."
                ),
                question=(
                    "Do the records establish name-plus-zip authentication, delivered "
                    "status, complete return/refund details, and explicit yes before the "
                    "air-purifier return?"
                ),
                policy_support=[
                    "official/policy.md::lines 10-16",
                    "official/policy.md::lines 116-126",
                ],
            ),
        )
        revisions.append(
            "corrected authentication route and added delivered-status/refund confirmation checks"
        )

    if case_id == "55":
        checklist["native"]["user_goal"] = {
            "text": (
                "Cancel Amelia's orders that have not arrived yet and, after listing the "
                "items in delivered orders, return all delivered items that can be returned."
            ),
            "support": [
                "derived/task.json::user_scenario.instructions.known_info",
                "derived/task.json::user_scenario.instructions.reason_for_call",
            ],
        }
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="policy_auth_and_confirmation",
                text=(
                    "Beyond native success, the retained record shows authentication via a "
                    "user-provided email before assistance; verifies pending status before "
                    "each cancellation and delivered status before each return; lists every "
                    "cancellation order/reason and every return order/item plus a "
                    "user-provided eligible refund method; and obtains explicit `yes` before "
                    "the updates. One aggregate confirmation is sufficient only when it "
                    "fully enumerates all actions and items being authorized."
                ),
                question=(
                    "Do the records establish authentication, each required status check, "
                    "complete cancellation/return/refund details, and an explicit yes that "
                    "unambiguously authorizes every ensuing update?"
                ),
                policy_support=[
                    "official/policy.md::lines 10-16",
                    "official/policy.md::lines 82-92",
                    "official/policy.md::lines 116-126",
                ],
            ),
        )
        revisions.extend(
            [
                "removed authentication workflow from native.user_goal",
                "added per-action status, cancellation reason, refund method, and fully enumerated confirmation checks",
            ]
        )

    if case_id == "63":
        checklist["native"]["user_goal"] = {
            "text": (
                "Handle Chen Johnson's initial poem-guess prompt, then tell him the bought "
                "Bluetooth speaker's price and battery life, replace that speaker in the "
                "pending order with the cheapest available Bluetooth speaker under $300 "
                "without cancelling the whole order, and confirm the new total."
            ),
            "support": ["derived/task.json::user_scenario.instructions.reason_for_call"],
        }
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="authenticate_before_disclosure_or_update",
                text=(
                    "Beyond native success, the retained record shows Chen Johnson, who "
                    "does not remember his email, was authenticated by name plus zip before "
                    "any user-specific order/product disclosure or update."
                ),
                question=(
                    "Was Chen authenticated by name plus zip before the first "
                    "user-specific lookup, disclosure, or update?"
                ),
                policy_support=["official/policy.md::lines 10-16"],
            ),
        )
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="explicit_yes_before_modify",
                text=(
                    "Beyond native success, the retained record shows the order was checked "
                    "as pending; the complete replacement item set, cheapest available "
                    "under-$300 speaker, and a user-provided or authorized price-difference "
                    "payment method were listed; the user was reminded to confirm all items; "
                    "and explicit `yes` was obtained before the single modification call."
                ),
                question=(
                    "Before modification, do the records establish pending status, the "
                    "complete replacement scope, payment authorization, completeness "
                    "reminder, and explicit yes?"
                ),
                policy_support=[
                    "official/policy.md::lines 16-16",
                    "official/policy.md::lines 82-84",
                    "official/policy.md::lines 94-98",
                    "official/policy.md::lines 108-114",
                ],
            ),
        )
        upsert_condition(
            checklist,
            condition(
                condition_id="policy_scoped_poem_response",
                text=(
                    "Beyond native success, the retained conversation shows that the agent "
                    "kept assistance within the retail policy when the user supplied the "
                    "opening line of a famous poem: it did not invent unsupported poem "
                    "content and then continued with the retail request when the user moved on."
                ),
                rationale=(
                    "The initial poem prompt is explicit case-specific task content, and the "
                    "policy prohibits making up information and limits the agent to the "
                    "listed retail assistance. None of the native DB or NL checks measures "
                    "this exchange."
                ),
                question=(
                    "Does the conversation show a policy-scoped, non-fabricated response to "
                    "the poem prompt followed by continuation to the retail task?"
                ),
                support=[
                    "derived/task.json::user_scenario.instructions.reason_for_call",
                    "official/policy.md::lines 3-8",
                    "official/policy.md::lines 18-24",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    EVALUATOR,
                ],
            ),
        )
        upsert_condition(
            checklist,
            condition(
                condition_id="never_cancel_entire_order",
                text=(
                    "Beyond native success, retained tool records show no "
                    "`cancel_pending_order` call for the entire order; if the requested "
                    "under-$300 replacement could not be made, the agent left the whole "
                    "order intact rather than cancelling it."
                ),
                rationale=(
                    "The official scenario says the user never wants the entire order "
                    "cancelled. A failed or non-persistent cancellation attempt can escape "
                    "the native final-DB comparison, so the action record is a separate "
                    "reviewable stronger measurement."
                ),
                question=(
                    "Do the retained tool records contain no whole-order cancellation call "
                    "and show that the user's no-cancellation instruction was respected?"
                ),
                support=[
                    "derived/task.json::user_scenario.instructions.reason_for_call",
                    "official/policy.md::Cancel pending order",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    EVALUATOR,
                    ENV_EVALUATOR,
                ],
            ),
        )
        revisions.extend(
            [
                "restored the initial poem prompt and no-whole-order-cancel intent to native.user_goal",
                "added policy-scoped poem handling stronger condition",
                "added no-whole-order-cancellation stronger condition",
                "corrected authentication route and added pending/item-completeness/payment checks",
            ]
        )

    if case_id == "85":
        checklist["native"]["user_goal"] = {
            "text": (
                "Help Yusuf Hernandez change his fleece jacket to the large red half-zip "
                "variant he wants."
            ),
            "support": [
                "derived/task.json::user_scenario.instructions.known_info",
                "derived/task.json::user_scenario.instructions.reason_for_call",
            ],
        }
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="policy_auth_and_confirm_before_modify",
                text=(
                    "Beyond native success, the retained record shows authentication via "
                    "Yusuf Hernandez's provided email (or name plus zip if the user supplies "
                    "that alternative); verifies the order is pending; lists the complete "
                    "fleece-jacket change and a user-provided or authorized payment method; "
                    "reminds the user to confirm all items; and obtains explicit `yes` before "
                    "the single item-modification call."
                ),
                question=(
                    "Do the records establish valid authentication, pending status, the "
                    "complete jacket/payment details, item-completeness reminder, and "
                    "explicit yes before modification?"
                ),
                policy_support=[
                    "official/policy.md::lines 10-16",
                    "official/policy.md::lines 82-84",
                    "official/policy.md::lines 94-98",
                    "official/policy.md::lines 108-114",
                ],
            ),
        )
        revisions.extend(
            [
                "removed policy authentication from native.user_goal",
                "added pending-status, complete-item-set, payment, and confirmation checks",
            ]
        )

    if case_id == "96":
        checklist["native"]["user_goal"] = {
            "text": (
                "Change Yusuf Li's pending LA order to the NYC address stored in another "
                "order without requiring him to reveal it, and replace the Bluetooth "
                "Speaker with the cheapest green variant."
            ),
            "support": [
                "derived/task.json::user_scenario.instructions.known_info",
                "derived/task.json::user_scenario.instructions.unknown_info",
                "derived/task.json::user_scenario.instructions.reason_for_call",
            ],
        }
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="policy_auth_and_confirmation",
                text=(
                    "Beyond native success, the retained record shows Yusuf Li, who does "
                    "not remember his email, was authenticated by name plus zip; the target "
                    "order was checked as pending; the address change and complete speaker "
                    "item change plus a user-provided or authorized price-difference payment "
                    "method were listed; the user was reminded to confirm all items; and "
                    "explicit `yes` was obtained before either modifying call."
                ),
                question=(
                    "Do the records establish name-plus-zip authentication, pending status, "
                    "complete address/item/payment scope, the item-completeness reminder, "
                    "and explicit yes before both updates?"
                ),
                policy_support=[
                    "official/policy.md::lines 10-16",
                    "official/policy.md::lines 82-84",
                    "official/policy.md::lines 94-114",
                ],
            ),
        )
        upsert_condition(
            checklist,
            condition(
                condition_id="address_lookup_privacy_preference",
                text=(
                    "Beyond native success, the retained record shows that the agent found "
                    "the NYC address in Yusuf Li's other order and did not require him to "
                    "reveal or restate that address."
                ),
                rationale=(
                    "The official user scenario explicitly states this privacy and lookup "
                    "preference, while native DB equality checks only the final address and "
                    "does not measure how the agent obtained it."
                ),
                question=(
                    "Does the conversation/tool record show the NYC address was obtained "
                    "from another order without asking the user to reveal or restate it?"
                ),
                support=[
                    "derived/task.json::user_scenario.instructions.reason_for_call",
                    "derived/artifact_inventory.json::artifact_classes[2].path_pattern",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    EVALUATOR,
                    ENV_EVALUATOR,
                ],
            ),
        )
        revisions.extend(
            [
                "removed policy authentication from native.user_goal",
                "added task-backed address privacy/lookup stronger condition",
                "corrected authentication route and added pending/item-completeness/payment checks",
            ]
        )

    if case_id == "104":
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="policy_auth_and_confirmation",
                text=(
                    "Beyond native success, the retained record shows authentication via "
                    "Lucas Brown's provided email (or name plus zip if user-supplied); "
                    "checks delivered status before each return and pending status before "
                    "the order modifications; fully lists every return item/order, the "
                    "address and red-item changes, and user-provided eligible refund/payment "
                    "methods; and obtains explicit `yes` before the updates. One aggregate "
                    "confirmation is sufficient only if it fully enumerates the complete "
                    "batch of actions and items."
                ),
                question=(
                    "Do the records establish authentication, all delivered/pending status "
                    "checks, complete return/modification/payment details, and explicit "
                    "authorization for every update?"
                ),
                policy_support=[
                    "official/policy.md::lines 10-16",
                    "official/policy.md::lines 82-84",
                    "official/policy.md::lines 94-126",
                ],
            ),
        )
        upsert_condition(
            checklist,
            condition(
                condition_id="chicago_address_lookup_privacy_preference",
                text=(
                    "Beyond native success, the retained record shows the agent retrieved "
                    "Lucas Brown's default Chicago home address from his authenticated "
                    "profile and did not require him to reveal or restate it."
                ),
                rationale=(
                    "The official scenario expressly requires profile lookup and protects "
                    "the address from user restatement, while final DB equality measures "
                    "only the resulting address."
                ),
                question=(
                    "Was the Chicago address obtained from the authenticated profile "
                    "without asking the user to reveal or restate it?"
                ),
                support=[
                    "derived/task.json::user_scenario.instructions.reason_for_call",
                    "derived/task.json::evaluation_criteria.reward_basis",
                    EVALUATOR,
                ],
            ),
        )
        revisions.extend(
            [
                "added delivered/pending status, payment, and fully enumerated confirmation checks",
                "added task-backed Chicago address lookup/privacy condition",
            ]
        )

    if case_id == "110":
        upsert_condition(
            checklist,
            workflow_condition(
                condition_id="policy_prereqs_before_updates",
                text=(
                    "Beyond native success, the retained record shows authentication via "
                    "Sophia Martin's provided email (or name plus zip if user-supplied); "
                    "checks each order is pending before its address/item modification; "
                    "lists the address, default-profile, and complete tablet-item changes "
                    "plus a user-provided or authorized price-difference payment method; "
                    "reminds the user to confirm all items; and obtains explicit `yes` "
                    "before the database updates."
                ),
                question=(
                    "Do the records establish valid authentication, each pending-status "
                    "check, complete address/profile/item/payment details, item-completeness "
                    "reminder, and explicit yes before the updates?"
                ),
                policy_support=[
                    "official/policy.md::lines 10-16",
                    "official/policy.md::lines 82-84",
                    "official/policy.md::lines 94-114",
                ],
            ),
        )
        revisions.append(
            "added per-order pending-status, complete-item-set, payment, and confirmation checks"
        )

    return revisions


def main() -> int:
    receipt_path = JOB_ROOT / "MANUAL_REVISION_RECEIPT.json"
    existing_receipt = load_json(receipt_path) if receipt_path.is_file() else None
    existing_cases = {
        str(item["case_id"]): item
        for item in (existing_receipt or {}).get("cases", [])
        if isinstance(item, dict) and item.get("case_id") is not None
    }
    receipt_cases: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        case_dir = RESULTS_ROOT / case_id
        json_path = case_dir / "checklist.json"
        yaml_path = case_dir / "checklist.yaml"
        checklist = load_json(json_path)
        before_json_sha256 = sha256_file(json_path)
        before_yaml_sha256 = sha256_file(yaml_path)
        prior = existing_cases.get(case_id)
        source_attempt, source_attempt_sha256 = generated_source_attempt(
            case_dir, checklist, prior
        )

        repair_native_artifact_rules(
            checklist, nl_assertion_count=task_nl_assertion_count(case_id)
        )
        semantic_revisions = repair_case_specific(case_id, checklist)

        write_json(json_path, checklist)
        write_yaml(yaml_path, checklist)
        if load_json(json_path) != load_yaml_as_json(yaml_path):
            raise ValueError(f"Canonical JSON/YAML mismatch after repair: {case_id}")
        receipt_cases.append(
            {
                "case_id": case_id,
                "source_generated_attempt": source_attempt,
                "source_generated_attempt_sha256": source_attempt_sha256,
                "before": {
                    "checklist_json_sha256": (
                        prior["before"]["checklist_json_sha256"]
                        if prior is not None
                        else before_json_sha256
                    ),
                    "checklist_yaml_sha256": (
                        prior["before"]["checklist_yaml_sha256"]
                        if prior is not None
                        else before_yaml_sha256
                    ),
                },
                "pre_system_design_revision": (
                    prior.get("pre_system_design_revision")
                    if prior is not None and prior.get("pre_system_design_revision")
                    else {
                        "checklist_json_sha256": before_json_sha256,
                        "checklist_yaml_sha256": before_yaml_sha256,
                    }
                ),
                "after": {
                    "checklist_json_sha256": sha256_file(json_path),
                    "checklist_yaml_sha256": sha256_file(yaml_path),
                    "case_packet_sha256": sha256_file(
                        PACKETS_ROOT / case_id / "case_packet.md"
                    ),
                    "raw_case_manifest_sha256": sha256_file(
                        PACKETS_ROOT / case_id / "raw_case_manifest.json"
                    ),
                },
                "common_revisions": [
                    "defined native success from the formal termination + DB + applicable NL components",
                    "excluded released scalar reward, runtime reward_basis/reward_breakdown, prior scores, and released labels from S/F/U evidence",
                    "bound decisive evidence to component fields in the unique case-matching simulations[*] record",
                    "made missing, misassociated, incomplete, or internally inconsistent component evidence undecided",
                    "kept policy/task requirements outside the native criterion as source-backed stronger conditions",
                ],
                "case_specific_revisions": semantic_revisions,
            }
        )

    receipt = {
        "schema_version": "tau3_remaining14_manual_draft_revision.v2",
        "created_at": (
            existing_receipt.get("created_at")
            if existing_receipt is not None
            else datetime.now(timezone.utc).isoformat()
        ),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "job_id": "tau3_remaining14_redraft_20260719",
        "scope": "canonical checklist.json/checklist.yaml only",
        "original_generated_attempts_preserved": True,
        "outcome_values_used_for_revision": False,
        "released_labels_used_for_revision": False,
        "native_evidence_independent_of_released_label": True,
        "stronger_measurement_reported_separately": True,
        "benchmark_conflict_requires_separate_source_pointer_review": True,
        "revision_basis": (
            "official task/user intent and policy, formal released evaluator semantics, "
            "outcome-free artifact inventory and state schema; no agent outcome, per-record "
            "released label, prior score, or record-specific evaluator result"
        ),
        "case_count": len(receipt_cases),
        "cases": receipt_cases,
    }
    write_json(receipt_path, receipt)
    print(f"repaired {len(receipt_cases)} canonical drafts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
