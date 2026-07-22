#!/usr/bin/env python3
"""Build the AppWorld test_normal-68 updated-standard checklist bundle.

This builder deliberately does not mutate the earlier v6 packet, remote-draft,
claim-freeze trees, or the system-design-v2 bundle. It reads only pre-run case
packets/checklists and official source material, applies the updated source-only
policy, and creates an independent 68-case packet/checklist/freeze namespace.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXPERIMENT = REPO_ROOT / (
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6"
)
SOURCE_PACKET_ROOT = SOURCE_EXPERIMENT / "case_packets/appworld"
SOURCE_DRAFT_ROOT = SOURCE_EXPERIMENT / (
    "remote_draft_runs/appworld68_tn_gpt54_high_c34_v2_20260719/results"
)
OUTPUT_ROOT = REPO_ROOT / (
    "experiments/appworld_test_normal_68_system_design_v3_gpt54_high_v1"
)
PRIOR_STANDARD_BUNDLE = REPO_ROOT / (
    "experiments/appworld_test_normal_68_system_design_v2_gpt54_high_v1"
)

SCHEMA_VERSION = "appworld_test_normal_68_system_design_v3.v1"
VISIBILITY_SCHEMA = "appworld_evidence_visibility_contract.v2"
STRONGER_REGISTRY_SCHEMA = "appworld_stronger_gap_registry.v4_system_design_v3"
PACKET_NATIVE_SCHEMA = "appworld_packet_native_registry.v4_system_design_v3"
PACKET_STRONGER_SCHEMA = "appworld_packet_stronger_gap_registry.v4_system_design_v3"
GENERATED_DATE = "2026-07-19"
EXPECTED_CASE_IDS_SHA256 = "2b54ce295ac44589ff9ceb689ea52daf69c64dfb0c76118db34af2b3e1da7c96"
FROZEN_EVALUATOR_SEMANTICS_SOURCE = REPO_ROOT / (
    "experiments/appworld_full_test_extension_v1/official_splits/"
    "appworld_evaluator_semantics.a072b7a8.json"
)
FROZEN_EVALUATOR_SEMANTICS_SOURCE_TREE = REPO_ROOT / (
    "experiments/appworld_full_test_extension_v1"
)
FROZEN_EVALUATOR_SEMANTICS_SHA256 = (
    "f92952e8a35001848126397fc43f4b612ea607030c53deb783af57d93e624d9f"
)

ACTION_CASE_IDS = frozenset(
    {
        "042a9fc_1",
        "042a9fc_2",
        "0d01c76_1",
        "0de03ea_1",
        "32616b5_1",
        "32616b5_2",
        "32616b5_3",
        "3b8fb7a_1",
        "59fae45_3",
        "634f342_2",
        "6b6ca61_1",
        "6f4b9a5_1",
        "6f4b9a5_2",
        "6f4b9a5_3",
        "8749218_1",
        "8749218_2",
        "9016950_3",
        "bde252e_2",
        "d194965_2",
        "f323bae_2",
        "f323bae_3",
        "f861c32_1",
        "f861c32_2",
        "fd1f8fa_1",
        "fd1f8fa_2",
        "fd1f8fa_3",
        "ffe6d5e_2",
    }
)

DELETE_ONLY_CASE_IDS = frozenset(
    {"f861c32_1", "f861c32_2", "fd1f8fa_1", "fd1f8fa_2", "fd1f8fa_3"}
)

MARKER_RE = re.compile(r"^\[appworld_stronger_gap_[0-9]{3}_[0-9a-f]{12}\]\s+")

NATIVE_SFU_RULE = (
    "Let each frozen registered test have an evidence status in {S, F, U}. "
    "Native S iff every registered test is S. Native F iff at least one "
    "registered test is F, regardless of unresolved remaining tests. Native U "
    "iff no registered test is F and at least one registered test is U."
)

STRONGER_SFU_RULE = {
    "condition": {
        "S": (
            "All conjuncts in condition.text are established by the condition's "
            "scorer-visible retained evidence."
        ),
        "F": "At least one conjunct is established false by retained evidence.",
        "U": (
            "No conjunct is established false, but at least one necessary conjunct "
            "is unresolved because evidence is missing, incomplete, or non-decisive."
        ),
    },
    "aggregate": {
        "S": "Every stronger condition is S.",
        "F": "At least one stronger condition is F.",
        "U": "No stronger condition is F and at least one is U.",
    },
    "action_absence_boundary": (
        "For a condition about whether an action occurred, absence is F only when "
        "the retained action/API trace is established complete; otherwise it is U."
    ),
    "separation": (
        "Stronger results are scored and reported independently. Stronger F does "
        "not change native S/F/U. Neither stronger F alone nor native S together "
        "with stronger F is sufficient to establish benchmark conflict; only the "
        "independent benchmark-conflict audit gate may do so."
    ),
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_object(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def yaml_bytes(value: Any) -> bytes:
    completed = subprocess.run(
        ["yq", "-P", "-o=yaml", ".", "-"],
        input=json_bytes(value),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "yq failed while rendering checklist YAML: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return completed.stdout


def yaml_tool_record() -> dict[str, Any]:
    binary = shutil.which("yq")
    if binary is None:
        raise RuntimeError("yq is required to render derived checklist YAML")
    completed = subprocess.run(
        [binary, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("could not identify yq YAML renderer")
    binary_path = Path(binary).resolve()
    return {
        "authoritative_format": "checklist.json",
        "derived_format": "checklist.yaml",
        "renderer": completed.stdout.decode("utf-8", errors="replace").strip(),
        "renderer_command": "yq -P -o=yaml . -",
        "renderer_binary_sha256": sha256_file(binary_path),
    }


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def condition(
    *,
    condition_id: str,
    text: str,
    rationale: str,
    artifact: str,
    question: str,
    support: list[str],
) -> dict[str, Any]:
    return {
        "id": condition_id,
        "text": " ".join(text.split()),
        "rationale": " ".join(rationale.split()),
        "decisive_artifacts": [
            {
                "artifact": " ".join(artifact.split()),
                "question": " ".join(question.split()),
                "support": support,
            }
        ],
        "support": support,
    }


def mark_conditions(raw_conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    marked: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_conditions, start=1):
        item = copy.deepcopy(raw)
        item["text"] = MARKER_RE.sub("", str(item["text"]))
        marker = f"[appworld_stronger_gap_{index:03d}_{sha256_object(item)[:12]}]"
        item["text"] = f"{marker} {item['text']}"
        marked.append(item)
    return marked


def visibility_contract() -> dict[str, Any]:
    return {
        "schema_version": VISIBILITY_SCHEMA,
        "known_before_run": True,
        "full_retained_record": {
            "rule": (
                "Preserve the benchmark execution artifacts, released evaluator "
                "label, complete TestTracker output, and evaluator report verbatim "
                "and immutably."
            ),
            "scorer_access": False,
        },
        "scorer_visible_non_verdict_evidence": {
            "projection_rule": (
                "Build an immutable scorer view with a fixed allowlist from the "
                "full retained record and frozen pre-run case sources."
            ),
            "criterion_and_target_basis": [
                "frozen_semantics/appworld_evaluator_semantics.a072b7a8.json",
                "official/specs.json",
                "official/ground_truth/evaluation.py",
                "official/ground_truth/test_data.json",
                "official/ground_truth/answer.json",
                "official/ground_truth/public_data.json",
                "official/ground_truth/private_data.json",
                "official/ground_truth/metadata.json",
                "official/dbs/**",
                "case-specific initial-state SQL column lists and evaluator "
                "model-field accesses in the official 19-file packet",
            ],
            "execution_evidence": [
                "retained submitted answer",
                "post-run database state or lossless start/end database diff",
                "API/action log",
                "environment/conversation trace",
                "LM/tool-call log",
                "verdict-free execution-status and termination evidence",
            ],
            "forbidden": [
                "released evaluator label or score",
                "TestTracker success, passes, failures, or num_tests output values",
                "evaluator report or component-evaluator output",
                "any summary, manifest, log field, reward, or aggregate that "
                "deterministically reveals a released result",
            ],
        },
        "non_scorer_released_results": {
            "rule": (
                "Only a non-scorer process may read these results after the native "
                "S/F/U verdict bytes and hash have been locked; they may never flow "
                "back to the scorer."
            ),
            "contents": [
                "released evaluator label",
                "complete TestTracker and evaluator outputs",
            ],
        },
        "native_verdict_rule": NATIVE_SFU_RULE,
        "benchmark_conflict_gate": {
            "review_scope": (
                "A separate record-level audit, independent of native and stronger "
                "evidence scoring."
            ),
            "mismatch_role": (
                "A released-label/native-verdict mismatch may be used as a review "
                "routing signal but is neither necessary nor sufficient for benchmark "
                "conflict."
            ),
            "confirmation_rule": (
                "Mark confirmed benchmark conflict only when retained artifacts and "
                "explicit source pointers establish that the original benchmark task, "
                "target construction, evaluator/oracle, or reward wiring/aggregation "
                "actually checked a different outcome from the benchmark's apparent "
                "claim."
            ),
        },
        "formal_semantics_binding": {
            "descriptor": "frozen_semantics/appworld_evaluator_semantics.a072b7a8.json",
            "descriptor_sha256": FROZEN_EVALUATOR_SEMANTICS_SHA256,
            "scope_note": (
                "The descriptor pins the released AppWorld commit and evaluator.py "
                "source hash. The case packet additionally freezes each case evaluator, "
                "test_data, targets, and initial-state SQL column inventory."
            ),
        },
        "stronger_rule": STRONGER_SFU_RULE,
    }


def repaired_native(old_native: dict[str, Any]) -> dict[str, Any]:
    native = copy.deepcopy(old_native)
    native["benchmark_success"]["rationale"] = (
        "The released AppWorld criterion is conjunctive over all frozen registered "
        f"tests. Evidence scoring uses the pre-locked aggregation rule: {NATIVE_SFU_RULE}"
    )
    native["checked_by"]["rationale"] = (
        "The frozen evaluator/oracle source defines the native criterion. Dynamic "
        "non-test attributes and per-record evaluator result outputs are excluded "
        "from evidence scoring."
    )
    artifact_support = [
        "official/specs.json::$.instruction",
        "official/ground_truth/evaluation.py::evaluate",
        "official/ground_truth/test_data.json::$",
        "official/ground_truth/public_data.json::$",
        "official/ground_truth/private_data.json::$",
        "official/ground_truth/metadata.json::$",
    ]
    native["decisive_artifacts"] = [
        {
            "artifact": (
                "Scorer-visible non-verdict AppWorld evidence only: frozen evaluator/"
                "oracle and target inputs, necessary initial-state and state-schema "
                "material, retained submitted answer, post-run database state or "
                "start/end diff, API/action logs, environment/conversation trace, "
                "LM/tool-call logs, and verdict-free execution-status evidence. "
                "Released evaluator labels, TestTracker result outputs, evaluator "
                "reports, and deterministic derivatives of those results are excluded."
            ),
            "question": (
                "Using only this scorer-visible bundle and the frozen evaluator "
                "semantics, is each registered test independently established as "
                "satisfied, established as unsatisfied, or unresolved?"
            ),
            "support": artifact_support,
        }
    ]
    rationale = (
        "Only scorer-visible non-verdict evidence may establish this registered-test "
        "outcome; released evaluator results are not evidence for native S/F/U."
    )
    for key in ("success_if", "fail_if"):
        for item in native[key]:
            item["rationale"] = rationale
    native["undecided_if"] = [
        {
            "text": (
                "Native U iff no frozen registered test is established as failed and "
                "at least one frozen registered-test outcome cannot be determined "
                "from scorer-visible non-verdict evidence."
            ),
            "support": [
                "official/ground_truth/evaluation.py::evaluate",
                "official/ground_truth/test_data.json::$",
            ],
            "rationale": (
                "Failure dominates uncertainty for this conjunctive native criterion: "
                "all S -> S; any F -> F; otherwise U. Missing or non-decisive evidence "
                "is never converted into pass or fail."
            ),
        }
    ]
    return native


def replacement_conditions(case_id: str) -> list[dict[str, Any]] | None:
    """Return source-reviewed markerless conditions, or None to inherit v2."""

    if case_id in DELETE_ONLY_CASE_IDS:
        return []

    evaluator = "official/ground_truth/evaluation.py::evaluate"
    specs = "official/specs.json::$.instruction"

    if case_id in {"042a9fc_1", "042a9fc_2"}:
        support = [
            specs,
            "official/dbs/phone.jsonl::L21",
            "official/dbs/phone.jsonl::L26",
            "official/ground_truth/private_data.json::$.to_add_song_ids",
            "official/ground_truth/private_data.json::$.to_remove_song_ids",
            evaluator,
        ]
        return [
            condition(
                condition_id="exact_playlist_change_multiplicity",
                text="""
                    Each add or remove directive in the relevant phone replies must
                    correspond one-to-one to exactly one task-created PlaylistSong
                    addition or removal in the identified playlist; no directive may
                    be omitted or duplicated, and no additional task-created
                    playlist-song change may be present.
                """,
                rationale="""
                    The phone replies specify individual change directives, while the
                    evaluator converts added and removed song IDs to sets and therefore
                    discards record multiplicity.
                """,
                artifact="""
                    Retained relevant phone replies, directive-to-song resolution, and
                    the complete task-created PlaylistSong database diff
                """,
                question="""
                    Is there an exact one-to-one multiset match between the source
                    directives and the additions/removals in the identified playlist?
                """,
                support=support,
            )
        ]

    if case_id == "0d01c76_1":
        support = [
            specs,
            "official/dbs/file_system.jsonl::L1-L196",
            "official/ground_truth/private_data.json::$.note_title_to_content",
            evaluator,
        ]
        return [
            condition(
                condition_id="exact_markdown_note_import",
                text="""
                    Every start-state Markdown File under
                    \"~/documents/personal/notes/\" must map one-to-one to exactly one
                    task-created SimpleNote Note whose title is the case-preserving
                    filename basename after removing only the final \".md\" extension
                    and replacing every ASCII underscore with one ASCII space, and
                    whose content is exactly equal to the source File.content with no
                    case, whitespace, or newline normalization.
                """,
                rationale="""
                    The instruction defines a deterministic file-to-note import, while
                    the evaluator compares titles and contents case-insensitively and
                    strips surrounding whitespace.
                """,
                artifact="""
                    Retained start-state Markdown-file inventory and contents plus the
                    complete task-created SimpleNote Note diff
                """,
                question="""
                    Is the source-file-to-note relation a bijection with the exact title
                    transformation and exact stored content equality?
                """,
                support=support,
            )
        ]

    if case_id == "0de03ea_1":
        support = [
            specs,
            "official/dbs/spotify.jsonl::L46-L65",
            "official/ground_truth/private_data.json::$.downloaded_song_ids",
            "official/ground_truth/private_data.json::$.collection_song_ids",
            evaluator,
        ]
        return [
            condition(
                condition_id="offline_nonrepeating_album_playback",
                text="""
                    The retained player must be playing, and beginning at its retained
                    current cursor, the next 900 seconds of playback must be supplied
                    entirely by distinct downloaded songs from one album in the user's
                    Spotify library, without exhausting the available queue or repeating
                    a song during that 900-second interval.
                """,
                rationale="""
                    The instruction requires actual offline, nonrepeating album playback
                    for fifteen minutes, while the evaluator checks only that designated
                    downloaded IDs occur somewhere in the queue and that no queued ID
                    lies outside the selected album collection.
                """,
                artifact="""
                    Retained final MusicPlayer state and cursor, ordered queue, song
                    durations, download membership, album membership, and library
                    membership
                """,
                question="""
                    Starting at the actual retained cursor, is there at least 900 seconds
                    of playing, downloaded, single-library-album, nonrepeating playback?
                """,
                support=support,
            )
        ]

    if case_id in {"32616b5_1", "32616b5_2", "32616b5_3"}:
        line_range = {"32616b5_1": "L1-L6", "32616b5_2": "L1-L8", "32616b5_3": "L1-L10"}[case_id]
        note_pointer = f"official/dbs/simple_note.jsonl::{line_range}"
        amount_support = [
            specs,
            note_pointer,
            "official/ground_truth/private_data.json::$.group_id_to_expense_amounts",
            "official/ground_truth/private_data.json::$.group_id_to_debtor_id_to_amounts",
            evaluator,
        ]
        description_support = [specs, note_pointer, evaluator]
        return [
            condition(
                condition_id="exact_splitwise_source_amounts",
                text="""
                    For every source expense represented in the applicable trip notes,
                    the corresponding task-created Expense.amount must exactly equal the
                    stated source total at currency precision, and every
                    ExpenseShare.share_amount joined to that Expense must exactly equal
                    the official currency-precision equal-share target, without the
                    evaluator's one-decimal rounding.
                """,
                rationale="""
                    The notes state the expense totals and equal-sharing obligations,
                    while the evaluator rounds Expense and ExpenseShare amounts to one
                    decimal place.
                """,
                artifact="""
                    Retained applicable source-note rows and joined task-created
                    Expense/ExpenseShare records with exact decimal comparisons
                """,
                question="""
                    Does every source expense have its exact total and exact official
                    currency-precision share amounts?
                """,
                support=amount_support,
            ),
            condition(
                condition_id="bind_expense_descriptions_to_source_rows",
                text="""
                    Every task-created Splitwise Expense must have a description exactly
                    equal to the quoted purpose in its corresponding applicable
                    source-note expense row.
                """,
                rationale="""
                    Each source row identifies what the expense was for, but the
                    evaluator does not inspect Expense.description.
                """,
                artifact="Retained applicable source-note rows and source-row-to-Expense join",
                question="""
                    Does every created Expense carry the exact quoted description from
                    its corresponding source row?
                """,
                support=description_support,
            ),
        ]

    if case_id == "3b8fb7a_1":
        common = [
            specs,
            "official/dbs/simple_note.jsonl::L1",
            "official/ground_truth/private_data.json::$.friend_venmo_id_to_money_i_owe",
            "official/ground_truth/private_data.json::$.friend_venmo_id_to_money_they_owe",
            evaluator,
        ]
        request_support = [specs, "official/dbs/simple_note.jsonl::L1", evaluator]
        return [
            condition(
                condition_id="private_exact_venmo_records",
                text="""
                    Every task-created Venmo Transaction for money the user owes must be
                    private, have an amount exactly equal to its source obligation, and
                    have description exactly \"For Maui trip\"; every task-created
                    PaymentRequest for money owed to the user must have an amount exactly
                    equal to its source obligation.
                """,
                rationale="""
                    The instruction fixes privacy, amounts, directions, and the Maui
                    description, while the evaluator rounds amounts to whole units, does
                    not check transaction privacy, and normalizes transaction descriptions.
                """,
                artifact="""
                    Retained Maui source note and complete task-created Transaction and
                    PaymentRequest records with exact field comparisons
                """,
                question="""
                    Do the task-created Venmo records have the required direction, exact
                    source amount, and required transaction privacy and description?
                """,
                support=common,
            ),
            condition(
                condition_id="payment_request_private_and_described",
                text="""
                    Every task-created Venmo PaymentRequest must be private and its
                    description must be exactly \"For Maui trip\".
                """,
                rationale="""
                    The instruction explicitly applies privacy and the Maui note to both
                    payments and requests, while the evaluator checks neither field on
                    PaymentRequest.
                """,
                artifact="Retained complete task-created Venmo PaymentRequest records",
                question="""
                    Is every task-created PaymentRequest private with description exactly
                    \"For Maui trip\"?
                """,
                support=request_support,
            ),
            condition(
                condition_id="one_record_per_maui_obligation",
                text="""
                    The task-created Venmo records must form a one-to-one correspondence
                    with the six obligations in the Maui source note: each \"I owe\" row
                    maps to exactly one Transaction and each \"owes me\" row maps to
                    exactly one PaymentRequest, with no obligation omitted, duplicated,
                    or combined.
                """,
                rationale="""
                    The source note lists six separate obligations, while receiver-keyed
                    evaluator dictionaries can overwrite duplicate records for the same
                    receiver.
                """,
                artifact="""
                    Retained Maui source rows and complete task-created Transaction and
                    PaymentRequest diff
                """,
                question="""
                    Is there exactly one correctly typed Venmo record for every source
                    obligation and no duplicate task record?
                """,
                support=common,
            ),
        ]

    if case_id == "59fae45_3":
        support = [
            specs,
            "official/ground_truth/private_data.json::$.playlist_id_to_updated_title",
            evaluator,
        ]
        return [
            condition(
                condition_id="case_preserving_exact_title_format",
                text="""
                    Every task-updated playlist title must be case-sensitively equal to
                    its original title followed by the exact ASCII delimiter \" | \" and
                    the official most-common-genre value, with no other prefix, suffix,
                    or delimiter change.
                """,
                rationale="""
                    The instruction explicitly supplies the title format, while the
                    evaluator uses normalized-text comparison and therefore does not
                    establish exact case or delimiter formatting.
                """,
                artifact="""
                    Retained start/end playlist-title mapping and official expected-title
                    mapping
                """,
                question="""
                    Is every final title exactly the case-preserving formatted title
                    required by the instruction?
                """,
                support=support,
            )
        ]

    if case_id == "634f342_2":
        first_support = [specs, evaluator]
        second_support = [
            specs,
            "official/dbs/file_system.jsonl::L1",
            "official/ground_truth/private_data.json::$.to_archive_song_ids",
            evaluator,
        ]
        return [
            condition(
                condition_id="bind_archived_songs_to_new_playlist",
                text="""
                    Every added PlaylistSong must belong to the single newly added
                    \"Old Songs\" playlist.
                """,
                rationale="""
                    The task binds archived songs to the new playlist, while the
                    evaluator checks the added song IDs without asserting their
                    playlist_id values.
                """,
                artifact="Retained added Playlist and PlaylistSong database diff",
                question="""
                    Does every added PlaylistSong reference the single newly added Old
                    Songs playlist?
                """,
                support=first_support,
            ),
            condition(
                condition_id="archive_each_source_song_exactly_once",
                text="""
                    The new \"Old Songs\" playlist must contain exactly one task-created
                    PlaylistSong for each distinct song entry in
                    \"~/documents/personal/songs_to_archive.txt\", with no omitted,
                    additional, or duplicate PlaylistSong.
                """,
                rationale="""
                    The source file lists the songs to put in the new playlist, while the
                    evaluator compares added song IDs as a set and therefore permits
                    duplicate additions.
                """,
                artifact="""
                    Retained songs-to-archive source file, resolved source-song IDs, new
                    playlist record, and complete task-created PlaylistSong diff
                """,
                question="""
                    Does the new playlist contain a one-to-one exact multiset projection
                    of the source file's distinct song entries?
                """,
                support=second_support,
            ),
        ]

    if case_id == "6b6ca61_1":
        amounts = [
            specs,
            "official/dbs/file_system.jsonl::L34",
            "official/ground_truth/private_data.json::$.venmo_user_id_to_amount",
            "official/ground_truth/private_data.json::$.splitwise_user_id_to_amount",
            evaluator,
        ]
        cardinality = [
            specs,
            "official/dbs/file_system.jsonl::L34",
            "official/ground_truth/private_data.json::$",
            evaluator,
        ]
        return [
            condition(
                condition_id="exact_csv_transaction_expense_amounts",
                text="""
                    For each data row in owe_list.csv, the task-created Venmo Transaction
                    or non-grouped Splitwise Expense and its corresponding ExpenseShare
                    must have an amount exactly equal to that row's CSV amount at currency
                    precision; this condition applies only to records created for the CSV
                    rows in this task.
                """,
                rationale="""
                    The CSV specifies row-level amounts, while the evaluator permits a
                    0.51 tolerance; limiting the condition to task-created
                    row-corresponding records prevents unrelated historical records from
                    entering the measurement.
                """,
                artifact="""
                    Retained owe_list.csv rows and complete task-created Venmo
                    Transaction, Splitwise Expense, and ExpenseShare records with exact
                    row joins
                """,
                question="""
                    Does every row-corresponding task-created monetary field exactly equal
                    its CSV amount?
                """,
                support=amounts,
            ),
            condition(
                condition_id="one_activity_per_csv_row",
                text="""
                    Each data row in owe_list.csv must correspond to exactly one
                    task-created activity: one private Venmo Transaction if that person
                    has a Venmo account, otherwise one non-grouped Splitwise Expense with
                    its one corresponding share and receipt; no row may be omitted,
                    duplicated, or processed through both branches.
                """,
                rationale="""
                    The instruction specifies one mutually exclusive action per CSV
                    person, while receiver- or payer-keyed evaluator dictionaries can
                    overwrite duplicate activities.
                """,
                artifact="""
                    Retained CSV rows, account-resolution evidence, and complete
                    task-created Transaction/Expense/ExpenseShare/receipt joins
                """,
                question="""
                    Is there exactly one correctly selected and fully bound activity for
                    every CSV data row?
                """,
                support=cardinality,
            ),
        ]

    if case_id in {"6f4b9a5_1", "6f4b9a5_2", "6f4b9a5_3"}:
        support = [
            specs,
            "official/dbs/simple_note.jsonl::L1",
            "official/ground_truth/private_data.json::$.song_name_to_artist_names",
            "official/ground_truth/private_data.json::$.song_name_to_release_month_str",
            evaluator,
        ]
        return [
            condition(
                condition_id="preserve_existing_release_log_rows",
                text="""
                    Every start-state liked-song row must correspond to exactly one final
                    liked-song row with the same song identity and artist multiset; every
                    already populated release-month value must remain unchanged, and every
                    TODO release-month value must be replaced by its official required
                    month. Lossless row reordering and formatting changes are allowed.
                """,
                rationale="""
                    The task asks to fill the missing month values in the existing log,
                    while the evaluator parses rows into normalized dictionaries that can
                    collapse duplicate rows. The task does not support byte identity or
                    stable row order.
                """,
                artifact="""
                    Retained start/end target-note contents, row-level semantic pairing,
                    and official song/artist/month mappings
                """,
                question="""
                    Is there a one-to-one semantic preservation of all source rows with
                    only TODO month values replaced by the required months?
                """,
                support=support,
            )
        ]

    if case_id in {"8749218_1", "8749218_2"}:
        support = [
            specs,
            "official/ground_truth/private_data.json::$.recommendation_song_ids",
            evaluator,
        ]
        return [
            condition(
                condition_id="executed_queue_shuffle",
                text="""
                    A retained Spotify shuffle operation must have been applied after
                    resetting the queue to all recommended songs and before playing it,
                    and the resulting queue must remain a complete value-level permutation
                    of the recommendation IDs. No particular permutation, including the
                    reverse sequence, is forbidden.
                """,
                rationale="""
                    The instruction requires executing shuffle, while the evaluator
                    converts the queue to a set and uses object identity for its order
                    checks. A reverse sequence can be a legitimate shuffle outcome and
                    must not be treated as an automatic failure.
                """,
                artifact="""
                    Retained complete Spotify action/API trace and ordered final
                    MusicPlayer queue
                """,
                question="""
                    Does the complete trace establish reset-then-shuffle-then-play, with
                    the final queue remaining a full permutation of all recommendations?
                """,
                support=support,
            )
        ]

    if case_id == "9016950_3":
        credential_support = [
            specs,
            "official/ground_truth/public_data.json::$.random_password",
            "official/ground_truth/private_data.json::$.no_account_admin_user_ids",
            evaluator,
        ]
        message_support = [
            specs,
            "official/ground_truth/public_data.json::$.message_text",
            "official/ground_truth/public_data.json::$.random_password",
            "official/ground_truth/private_data.json::$.no_account_phone_user_ids",
            evaluator,
        ]
        return [
            condition(
                condition_id="validate_new_account_credential",
                text="""
                    Every expected task-created parent Venmo account must have been
                    created with a case-sensitive credential exactly equal to
                    public_data.random_password.
                """,
                rationale="""
                    The instruction specifies the account credential, while the evaluator
                    checks only the added users' email/name mapping. A post-hoc login probe
                    and a rule forbidding retention of credential values are
                    evidence-governance choices, not task-outcome requirements.
                """,
                artifact="""
                    Retained account-creation call/state evidence or a predeclared
                    redacted case-sensitive equality result binding the supplied
                    credential to public_data.random_password
                """,
                question="""
                    Does credential evidence establish case-sensitive equality to the
                    instruction-specified password for every expected created account?
                """,
                support=credential_support,
            ),
            condition(
                condition_id="sms_credential_exact_binding",
                text="""
                    For every expected task-created account, the corresponding outbound
                    phone message must be case-sensitively and character-for-character
                    equal to public_data.message_text, including the same
                    instruction-specified credential.
                """,
                rationale="""
                    The quoted message and password are case-specific, while the evaluator
                    compares message text with ignore_case=True.
                """,
                artifact="""
                    Retained task-created GlobalTextMessage records joined to the expected
                    parent phone recipients
                """,
                question="""
                    Does every corresponding outbound message exactly equal the official
                    message text with the same case-sensitive credential?
                """,
                support=message_support,
            ),
        ]

    if case_id == "bde252e_2":
        support = [
            specs,
            "official/dbs/todoist.jsonl::L15-L112",
            "official/ground_truth/private_data.json::$.to_delete_inbox_task_ids",
            evaluator,
        ]
        return [
            condition(
                condition_id="preserve_all_user_visible_task_fields",
                text="""
                    There must be a one-to-one pairing between each task removed from
                    Inbox for movement and each task added to \"Today's Target\". Within
                    every pair, user_id, section_id, title, description, due_date,
                    priority, duration, duration_unit, is_completed, assignee_id, and
                    assigner_id must be equal. Only id, project_id, created_at,
                    record_hash, and project-local order_index may differ.
                """,
                rationale="""
                    The instruction requires the moved tasks to be identical apart from
                    their project, while the evaluator checks only title/description,
                    duration, and priority and uses title-keyed dictionaries that do not
                    establish a complete record bijection.
                """,
                artifact="""
                    Retained complete start-state removed-Inbox Task records and end-state
                    added-target Task records with schema-aware one-to-one field comparison
                """,
                question="""
                    Does every moved-task pair preserve every enumerated task field, with
                    differences confined to the explicitly allowed identity/project/system
                    fields?
                """,
                support=support,
            )
        ]

    if case_id == "d194965_2":
        support = [
            specs,
            "official/dbs/simple_note.jsonl::L1",
            "official/ground_truth/private_data.json::$.song_ids",
            "official/ground_truth/public_data.json::$.playlist_title",
            evaluator,
        ]
        return [
            condition(
                condition_id="new_playlist_membership_multiset_exact",
                text="""
                    The single task-created \"Songs from Simple Note\" playlist must
                    contain exactly one PlaylistSong for each song line in the source
                    SimpleNote note, with no omitted, additional, or duplicate playlist
                    membership.
                """,
                rationale="""
                    The source note enumerates the playlist contents, while the evaluator
                    converts playlist song IDs to a set and therefore discards multiplicity.
                """,
                artifact="""
                    Retained source SimpleNote song lines, resolved source-song IDs, and
                    the complete task-created playlist membership
                """,
                question="""
                    Is the new playlist's song-ID multiset exactly the one-to-one
                    projection of the source-note lines?
                """,
                support=support,
            )
        ]

    if case_id in {"f323bae_2", "f323bae_3"}:
        support = [
            specs,
            "official/ground_truth/private_data.json::$.header_row",
            evaluator,
        ]
        return [
            condition(
                condition_id="exact_lowercase_date_header",
                text="""
                    After applying the released evaluator's frozen parse procedure --
                    strip the file content, split on newline, split each row on ASCII
                    comma, replace underscores with spaces, and strip each field -- the
                    first header field must be case-sensitively equal to the
                    five-character string \"date\".
                """,
                rationale="""
                    The instruction explicitly fixes the first header name as lowercase
                    \"date\", while the evaluator compares the parsed header with
                    ignore_case=True.
                """,
                artifact="""
                    Retained task-created CSV bytes and deterministic application of the
                    released evaluator's frozen field parse to the first header field
                """,
                question="Is the parsed first header field exactly lowercase \"date\"?",
                support=support,
            )
        ]

    if case_id == "ffe6d5e_2":
        support = [
            specs,
            "official/dbs/simple_note.jsonl::L2",
            "official/ground_truth/private_data.json::$.favorite_recipe_names",
            evaluator,
        ]
        return [
            condition(
                condition_id="recipe_name_only_message",
                text="""
                    Under the same released normalize_text comparison semantics used by
                    the native evaluator, the whole outbound message must equal exactly
                    one official favorite-recipe name; no additional normalized token or
                    punctuation may remain.
                """,
                rationale="""
                    \"Just the name, nothing else\" requires whole-message equality to a
                    favorite recipe name, while the evaluator permits a message merely
                    containing an accepted name. Reusing the released comparator avoids
                    adding a reviewer-defined raw case or spacing requirement.
                """,
                artifact="""
                    Retained outbound GlobalTextMessage and official favorite-recipe-name
                    inventory with the released normalize_text whole-string comparison
                """,
                question="""
                    Does the whole normalized message equal exactly one normalized
                    favorite recipe name and nothing else?
                """,
                support=support,
            )
        ]

    return None


def extract_old_native_registry(packet_text: str) -> dict[str, Any]:
    section_start = packet_text.index("### Machine-verifiable registered-test registry")
    section_end = packet_text.index("### Machine-verifiable stronger-gap registry")
    section = packet_text[section_start:section_end]
    match = re.search(r"```json\n(.*?)\n```", section, flags=re.DOTALL)
    if match is None:
        raise RuntimeError("could not parse old packet native registry")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict) or not isinstance(payload.get("registered_tests"), list):
        raise RuntimeError("old packet native registry is malformed")
    return payload


def render_packet_header(
    *,
    native_registry: dict[str, Any],
    case_entry: dict[str, Any],
    registry_canonical_json_sha256: str,
    registry_file_sha256: str,
    visibility: dict[str, Any],
    evaluator_semantics: dict[str, Any],
) -> str:
    stronger_payload = {
        "schema_version": PACKET_STRONGER_SCHEMA,
        "registry_source_bundle_relative": "stronger_registry.json",
        "registry_canonical_json_sha256": registry_canonical_json_sha256,
        "registry_file_sha256": registry_file_sha256,
        "canonicalization": "UTF-8 JSON, ensure_ascii=true, sort_keys=true, separators=(',', ':')",
        "condition_verdict_rule": STRONGER_SFU_RULE,
        "case": case_entry,
    }
    return "\n".join(
        [
            "## Frozen AppWorld Source-Only Evidence Checklist Contract (Mandatory)",
            "",
            "This contract and the case-specific checklist are locked before access to any agent outcome, per-record released evaluator label, or component evaluator result.",
            "",
            f"- Contract schema: `{SCHEMA_VERSION}`",
            f"- Visibility schema: `{VISIBILITY_SCHEMA}`",
            "- Native criterion authority: the released evaluator/oracle formal semantics represented by the frozen registered tests below.",
            "- Official case-specific obligations beyond that native criterion may appear only in the separately reported stronger registry.",
            "- Reviewer preferences without case-specific official support are excluded.",
            "",
            "### Artifact visibility and phase separation",
            "",
            "The complete benchmark record and released result remain preserved, but the S/F/U scorer receives only the allowlisted non-verdict view. The released result is read only after the scorer verdict bytes and hash are locked.",
            "",
            "```json",
            json.dumps(visibility, ensure_ascii=False, indent=2),
            "```",
            "",
            "### Released evaluator semantic binding",
            "",
            "The following pre-run descriptor binds the TestTracker registration/aggregation semantics to the released AppWorld commit and evaluator source hash. It contains formal source definitions, not any per-record result value.",
            "",
            f"- Bundle-relative descriptor: `frozen_semantics/{FROZEN_EVALUATOR_SEMANTICS_SOURCE.name}`",
            f"- Descriptor file SHA-256: `{FROZEN_EVALUATOR_SEMANTICS_SHA256}`",
            "",
            "```json",
            json.dumps(evaluator_semantics, ensure_ascii=False, indent=2),
            "```",
            "",
            "### Machine-verifiable native registry",
            "",
            "Copy `required_native` exactly as the complete `native` object. Native S/F/U is an evidence verdict over the frozen native criterion; it is not copied from or inferred from any released evaluator result.",
            "",
            "```json",
            json.dumps(native_registry, ensure_ascii=False, indent=2),
            "```",
            "",
            "### Machine-verifiable stronger registry",
            "",
            "Copy `case.gaps[*].required_condition` exactly, in order, into `stronger.additional_conditions`. If `case.gaps` is empty, the stronger list must be empty. Score and report stronger independently. Neither stronger F alone nor native S together with stronger F is sufficient to establish benchmark conflict; only the separate record-level benchmark-conflict audit may confirm it.",
            "",
            "```json",
            json.dumps(stronger_payload, ensure_ascii=False, indent=2),
            "```",
        ]
    )


def replace_packet_contract(old_packet: str, new_header: str) -> str:
    old_start = old_packet.index("## Frozen AppWorld Native Scoring Semantics (Mandatory)")
    source_start = old_packet.index("## Source Inventory")
    prefix = old_packet[:old_start].rstrip()
    tail = old_packet[source_start:]
    return f"{prefix}\n\n{new_header}\n\n{tail}"


def validate_condition_shape(value: dict[str, Any], *, case_id: str) -> None:
    expected = {"id", "text", "rationale", "decisive_artifacts", "support"}
    if set(value) != expected:
        raise RuntimeError(f"{case_id}: invalid stronger condition fields")
    if not MARKER_RE.match(value["text"]):
        raise RuntimeError(f"{case_id}: stronger marker missing")
    if not value["decisive_artifacts"] or not value["support"]:
        raise RuntimeError(f"{case_id}: stronger condition lacks evidence/support")


def validate_repaired_checklist(checklist: dict[str, Any], *, case_id: str) -> None:
    if checklist.get("schema_version") != "case_checklist_v1":
        raise RuntimeError(f"{case_id}: checklist schema drift")
    if checklist.get("case_unit_id") != case_id or checklist.get("task_id") != case_id:
        raise RuntimeError(f"{case_id}: checklist identity drift")
    native = checklist["native"]
    artifact_text = json.dumps(native["decisive_artifacts"], ensure_ascii=False)
    required_phrases = (
        "Scorer-visible non-verdict AppWorld evidence only",
        "Released evaluator labels",
        "TestTracker result outputs",
        "are excluded",
    )
    if not all(phrase in artifact_text for phrase in required_phrases):
        raise RuntimeError(f"{case_id}: native artifact isolation contract missing")
    if "official TestTracker results" in artifact_text:
        raise RuntimeError(f"{case_id}: old decisive result dependency remains")
    if len(native["undecided_if"]) != 1 or "Native U iff" not in native["undecided_if"][0]["text"]:
        raise RuntimeError(f"{case_id}: native U rule missing")
    if NATIVE_SFU_RULE not in native["benchmark_success"]["rationale"]:
        raise RuntimeError(f"{case_id}: native aggregate rule missing")
    for item in native["success_if"] + native["fail_if"]:
        if "non-verdict evidence" not in item["rationale"]:
            raise RuntimeError(f"{case_id}: per-test independence rationale missing")
    conditions = checklist["stronger"]["additional_conditions"]
    for value in conditions:
        validate_condition_shape(value, case_id=case_id)


def tree_index(root: Path, *, omit: set[str] | None = None) -> list[dict[str, Any]]:
    omitted = omit or set()
    records = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in omitted:
            continue
        records.append(
            {"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
        )
    return records


def compare_trees(expected: Path, observed: Path) -> None:
    expected_index = tree_index(expected)
    observed_index = tree_index(observed)
    if expected_index != observed_index:
        expected_map = {item["path"]: item for item in expected_index}
        observed_map = {item["path"]: item for item in observed_index}
        changed = sorted(
            path
            for path in set(expected_map) | set(observed_map)
            if expected_map.get(path) != observed_map.get(path)
        )
        raise RuntimeError(
            f"output tree does not match deterministic rebuild ({len(changed)} paths): "
            + ", ".join(changed[:20])
        )


def materialize(root: Path) -> dict[str, Any]:
    source_checklists = sorted(SOURCE_DRAFT_ROOT.glob("*/checklist.json"))
    case_ids = [path.parent.name for path in source_checklists]
    if len(case_ids) != 68 or len(set(case_ids)) != 68:
        raise RuntimeError(f"expected exactly 68 source checklists, found {len(case_ids)}")
    if sha256_object(case_ids) != EXPECTED_CASE_IDS_SHA256:
        raise RuntimeError("source cohort case-ID closure differs from the frozen 68-case set")
    if not ACTION_CASE_IDS <= set(case_ids):
        raise RuntimeError("reviewed action cases are not a subset of the 68-case source cohort")
    prior_result_ids = {
        path.parent.name
        for path in (PRIOR_STANDARD_BUNDLE / "results").glob("*/checklist.json")
    }
    if prior_result_ids != set(case_ids):
        raise RuntimeError("prior-standard bundle does not contain the frozen 68-case set")

    if (
        not FROZEN_EVALUATOR_SEMANTICS_SOURCE.is_file()
        or sha256_file(FROZEN_EVALUATOR_SEMANTICS_SOURCE)
        != FROZEN_EVALUATOR_SEMANTICS_SHA256
    ):
        raise RuntimeError("frozen AppWorld evaluator-semantics descriptor drift")
    evaluator_semantics = json.loads(
        FROZEN_EVALUATOR_SEMANTICS_SOURCE.read_text(encoding="utf-8")
    )
    semantics_output = root / "frozen_semantics" / FROZEN_EVALUATOR_SEMANTICS_SOURCE.name
    semantics_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FROZEN_EVALUATOR_SEMANTICS_SOURCE, semantics_output)

    visibility = visibility_contract()
    visibility_file_bytes = json_bytes(visibility)
    write_bytes(root / "artifact_visibility_contract.json", visibility_file_bytes)

    repaired: dict[str, dict[str, Any]] = {}
    native_registries: dict[str, dict[str, Any]] = {}
    source_records: dict[str, dict[str, Any]] = {}
    registry_cases: list[dict[str, Any]] = []
    changed_stronger_case_ids: set[str] = set()

    for case_id in case_ids:
        source_checklist_path = SOURCE_DRAFT_ROOT / case_id / "checklist.json"
        source_packet_dir = SOURCE_PACKET_ROOT / case_id
        source_packet_path = source_packet_dir / "case_packet.md"
        old_checklist = json.loads(source_checklist_path.read_text(encoding="utf-8"))
        old_packet = source_packet_path.read_text(encoding="utf-8")
        old_registry = extract_old_native_registry(old_packet)
        if old_registry.get("required_native") != old_checklist.get("native"):
            raise RuntimeError(f"{case_id}: source packet native projection differs from source draft")
        raw_manifest_path = source_packet_dir / "raw_case_manifest.json"
        raw_manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
        packet_files = raw_manifest.get("packet_files")
        source_hashes = raw_manifest.get("sha256_per_file")
        if (
            raw_manifest.get("case_unit_id") != case_id
            or not isinstance(packet_files, list)
            or len(packet_files) != 19
            or len(set(packet_files)) != 19
            or not isinstance(source_hashes, dict)
            or set(packet_files) != set(source_hashes)
            or any(
                not isinstance(relative, str)
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
                or Path(relative).as_posix() != relative
                for relative in packet_files
            )
        ):
            raise RuntimeError(f"{case_id}: source raw manifest identity/inventory drift")
        raw_case_root = source_packet_dir / "raw_case"
        actual_raw_files = sorted(
            path.relative_to(raw_case_root).as_posix()
            for path in raw_case_root.rglob("*")
            if path.is_file()
        )
        if actual_raw_files != sorted(packet_files):
            raise RuntimeError(
                f"{case_id}: source raw tree contains unregistered or missing files"
            )
        for relative in packet_files:
            source_file = raw_case_root / relative
            if not source_file.is_file() or sha256_file(source_file) != source_hashes[relative]:
                raise RuntimeError(f"{case_id}: source raw file hash drift: {relative}")

        new_checklist = copy.deepcopy(old_checklist)
        new_checklist["native"] = repaired_native(old_checklist["native"])
        override = replacement_conditions(case_id)
        if override is None:
            old_conditions = old_checklist["stronger"]["additional_conditions"]
            new_conditions = mark_conditions(old_conditions)
            disposition = "reviewed_unchanged_source_supported"
        else:
            new_conditions = mark_conditions(override)
            disposition = (
                "reviewed_no_gap" if not new_conditions else "reviewed_repaired_source_supported"
            )
        if new_conditions != old_checklist["stronger"]["additional_conditions"]:
            changed_stronger_case_ids.add(case_id)
        new_checklist["stronger"] = {"additional_conditions": new_conditions}
        validate_repaired_checklist(new_checklist, case_id=case_id)
        repaired[case_id] = new_checklist

        native_registry = {
            "schema_version": PACKET_NATIVE_SCHEMA,
            "case_unit_id": case_id,
            "all_tests_marker": old_registry["all_tests_marker"],
            "registered_tests": old_registry["registered_tests"],
            "registered_test_count": len(old_registry["registered_tests"]),
            "native_verdict_rule": NATIVE_SFU_RULE,
            "required_native": new_checklist["native"],
        }
        native_registries[case_id] = native_registry
        registry_cases.append(
            {
                "case_unit_id": case_id,
                "dataset_name": "test_normal",
                "review_disposition": disposition,
                "native_registry_canonical_json_sha256": sha256_object(native_registry),
                "gaps": [
                    {
                        "index": index,
                        "marker": item["text"].split(" ", 1)[0],
                        "required_condition": item,
                    }
                    for index, item in enumerate(new_conditions, start=1)
                ],
            }
        )
        source_records[case_id] = {
            "source_checklist_path": source_checklist_path.relative_to(REPO_ROOT).as_posix(),
            "source_checklist_sha256": sha256_file(source_checklist_path),
            "source_packet_path": source_packet_path.relative_to(REPO_ROOT).as_posix(),
            "source_packet_sha256": sha256_file(source_packet_path),
            "official_source_manifest_sha256": sha256_file(
                source_packet_dir / "raw_case_manifest.json"
            ),
        }

    if changed_stronger_case_ids != set(ACTION_CASE_IDS):
        raise RuntimeError(
            "actual stronger changed-case set differs from reviewed action set: "
            f"actual={sorted(changed_stronger_case_ids)}"
        )

    stronger_registry = {
        "schema_version": STRONGER_REGISTRY_SCHEMA,
        "review_date": GENERATED_DATE,
        "review_mode": "source_only_outcome_blind",
        "scope": {
            "dataset_name": "test_normal",
            "case_count": 68,
            "action_case_count": len(ACTION_CASE_IDS),
            "explicitly_deleted_unsupported_case_count": len(DELETE_ONLY_CASE_IDS),
        },
        "review_rule": (
            "Record only concrete case-specific official task, user-intent, or policy "
            "obligations not fully operationalized by the released evaluator/oracle. "
            "Exclude reviewer preferences and all agent outcomes or released results."
        ),
        "condition_verdict_rule": STRONGER_SFU_RULE,
        "cases": registry_cases,
    }
    registry_canonical_sha = sha256_object(stronger_registry)
    registry_file_bytes = json_bytes(stronger_registry)
    registry_file_sha = sha256_bytes(registry_file_bytes)
    write_bytes(root / "stronger_registry.json", registry_file_bytes)

    output_records: list[dict[str, Any]] = []
    for case_id in case_ids:
        source_packet_dir = SOURCE_PACKET_ROOT / case_id
        output_packet_dir = root / "case_packets/appworld" / case_id
        shutil.copytree(source_packet_dir / "raw_case", output_packet_dir / "raw_case")
        shutil.copy2(
            source_packet_dir / "raw_case_manifest.json",
            output_packet_dir / "raw_case_manifest.json",
        )
        case_entry = next(item for item in registry_cases if item["case_unit_id"] == case_id)
        old_packet = (source_packet_dir / "case_packet.md").read_text(encoding="utf-8")
        header = render_packet_header(
            native_registry=native_registries[case_id],
            case_entry=case_entry,
            registry_canonical_json_sha256=registry_canonical_sha,
            registry_file_sha256=registry_file_sha,
            visibility=visibility,
            evaluator_semantics=evaluator_semantics,
        )
        new_packet = replace_packet_contract(old_packet, header)
        write_bytes(output_packet_dir / "case_packet.md", new_packet.encode("utf-8"))

        result_dir = root / "results" / case_id
        checklist_json = json_bytes(repaired[case_id])
        checklist_yaml = yaml_bytes(repaired[case_id])
        prior_result_dir = PRIOR_STANDARD_BUNDLE / "results" / case_id
        if (
            checklist_json != (prior_result_dir / "checklist.json").read_bytes()
            or checklist_yaml != (prior_result_dir / "checklist.yaml").read_bytes()
        ):
            raise RuntimeError(
                f"{case_id}: updated standard unexpectedly changed case-specific draft bytes"
            )
        write_bytes(result_dir / "checklist.json", checklist_json)
        write_bytes(result_dir / "checklist.yaml", checklist_yaml)
        record = {
            "schema_version": "appworld_checklist_repair_record.v2_standard_update",
            "case_unit_id": case_id,
            "dataset_name": "test_normal",
            "repair_mode": "source_only_outcome_blind_updated_standard_refreeze",
            "source": source_records[case_id],
            "prior_standard": {
                "bundle_relative_path": PRIOR_STANDARD_BUNDLE.relative_to(
                    REPO_ROOT
                ).as_posix(),
                "checklist_json_sha256": sha256_file(
                    prior_result_dir / "checklist.json"
                ),
                "checklist_yaml_sha256": sha256_file(
                    prior_result_dir / "checklist.yaml"
                ),
                "case_specific_content_changed": False,
            },
            "output": {
                "checklist_json_sha256": sha256_bytes(checklist_json),
                "checklist_yaml_sha256": sha256_bytes(checklist_yaml),
                "case_packet_sha256": sha256_bytes(new_packet.encode("utf-8")),
                "native_registry_canonical_json_sha256": sha256_object(
                    native_registries[case_id]
                ),
                "stronger_condition_ids": [
                    item["id"]
                    for item in repaired[case_id]["stronger"]["additional_conditions"]
                ],
            },
            "outcome_or_released_result_inputs_read": [],
        }
        write_bytes(result_dir / "repair_record.json", json_bytes(record))
        output_records.append(record)

    condition_count = sum(
        len(item["stronger"]["additional_conditions"]) for item in repaired.values()
    )
    gap_case_count = sum(
        bool(item["stronger"]["additional_conditions"]) for item in repaired.values()
    )
    registered_test_count = sum(
        len(item["registered_tests"]) for item in native_registries.values()
    )
    if (gap_case_count, 68 - gap_case_count, condition_count, registered_test_count) != (
        34,
        34,
        44,
        469,
    ):
        raise RuntimeError(
            "reviewed count drift: "
            f"gap={gap_case_count}, no_gap={68-gap_case_count}, "
            f"conditions={condition_count}, tests={registered_test_count}"
        )

    experiment_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "source_only_updated_standard_refrozen",
        "created_date": GENERATED_DATE,
        "scope": {
            "benchmark": "AppWorld",
            "dataset_name": "test_normal",
            "case_count": 68,
            "case_ids": case_ids,
            "case_ids_sha256": sha256_object(case_ids),
            "registered_test_count": registered_test_count,
        },
        "base_draft_generation": {
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "fast_mode": False,
            "requested_parallelism": 34,
            "source_results_root": SOURCE_DRAFT_ROOT.relative_to(REPO_ROOT).as_posix(),
        },
        "repair": {
            "mode": "deterministic_source_only_outcome_blind_standard_update",
            "prior_standard_bundle": PRIOR_STANDARD_BUNDLE.relative_to(
                REPO_ROOT
            ).as_posix(),
            "case_specific_draft_content_revalidated_case_count": 68,
            "case_specific_draft_content_changed_case_count": 0,
            "packet_global_contract_changed_case_count": 68,
            "native_artifact_contract_preserved_case_count": 68,
            "native_explicit_sfu_rule_preserved_case_count": 68,
            "stronger_condition_content_changed_case_count": 0,
            "stronger_reviewed_prior_action_case_count": len(ACTION_CASE_IDS),
            "stronger_gap_case_count": gap_case_count,
            "stronger_no_gap_case_count": 68 - gap_case_count,
            "stronger_condition_count": condition_count,
            "old_frozen_namespace_mutated": False,
            "outcome_or_released_result_inputs_read": [],
        },
        "pipeline_integration": {
            "status": "required_gates_not_implemented_by_this_asset_repair",
            "safe_to_score_with_unfiltered_reference_workspace_copy": False,
            "safe_to_score_with_current_reference_prompt": False,
            "known_reference_runner_gaps": [
                {
                    "gate": "post_lock_released_result_join",
                    "source": "neurips_ed_track_minimal/scripts/score_evidence_with_codex.py",
                    "issue": (
                        "The current runner resolves the released evaluator label "
                        "before invoking the scorer instead of joining it only after "
                        "the native verdict bytes and hash are locked."
                    ),
                },
                {
                    "gate": "allowlist_scorer_view",
                    "source": "neurips_ed_track_minimal/scripts/score_evidence_with_codex.py",
                    "issue": (
                        "The current runner copies the complete evidence directory "
                        "instead of constructing the contract's non-verdict allowlist."
                    ),
                },
                {
                    "gate": "independent_stronger_scoring",
                    "source": "neurips_ed_track_minimal/prompts/score_evidence_with_codex.prompt.md",
                    "issue": (
                        "The current prompt derives stronger F from native F and "
                        "stronger U from native U instead of independently applying "
                        "each locked stronger condition to retained evidence."
                    ),
                },
                {
                    "gate": "independent_benchmark_conflict_audit",
                    "source": "neurips_ed_track_minimal/",
                    "issue": (
                        "No AppWorld record-level confirmed-conflict audit implements "
                        "the retained-artifact plus explicit-source-pointer gate "
                        "independently of mismatch and native/stronger verdict routing."
                    ),
                },
            ],
            "required_next_gates": [
                "Move released-result resolution and comparison after the native "
                "verdict bytes and hash are locked.",
                "Implement and validate an allowlist-built non-verdict scorer view.",
                "Replace native-conditioned stronger verdict propagation with "
                "independent per-condition stronger S/F/U scoring.",
                "Implement an AppWorld record-level benchmark-conflict audit in "
                "which mismatch is neither necessary nor sufficient and confirmation "
                "requires retained-artifact and explicit source-pointer proof of a "
                "different checked outcome.",
            ],
        },
        "hash_canonicalization": (
            "UTF-8 JSON, ensure_ascii=true, sort_keys=true, separators=(',', ':')"
        ),
        "artifact_visibility_contract_canonical_json_sha256": sha256_object(visibility),
        "artifact_visibility_contract_file_sha256": sha256_bytes(visibility_file_bytes),
        "stronger_registry_canonical_json_sha256": registry_canonical_sha,
        "stronger_registry_file_sha256": registry_file_sha,
        "frozen_evaluator_semantics_file_sha256": FROZEN_EVALUATOR_SEMANTICS_SHA256,
        "yaml_derivation": yaml_tool_record(),
    }
    write_bytes(root / "experiment_manifest.json", json_bytes(experiment_manifest))

    freeze_records = []
    for case_id in case_ids:
        source_dir = root / "results" / case_id
        freeze_dir = root / "claim_freeze/checklists" / case_id
        freeze_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_dir / "checklist.json", freeze_dir / "checklist.json")
        shutil.copy2(source_dir / "checklist.yaml", freeze_dir / "checklist.yaml")
        freeze_records.append(
            {
                "case_unit_id": case_id,
                "checklist_json_sha256": sha256_file(freeze_dir / "checklist.json"),
                "checklist_yaml_sha256": sha256_file(freeze_dir / "checklist.yaml"),
                "case_packet_sha256": sha256_file(
                    root / "case_packets/appworld" / case_id / "case_packet.md"
                ),
            }
        )
    freeze_manifest = {
        "schema_version": "appworld_pre_outcome_checklist_freeze.v2_standard_update",
        "created_date": GENERATED_DATE,
        "case_count": 68,
        "lock_boundary": (
            "Before access to agent outcomes, per-record released evaluator labels, "
            "or component evaluator results."
        ),
        "records": freeze_records,
        "records_sha256": sha256_object(freeze_records),
    }
    write_bytes(root / "claim_freeze/freeze_manifest.json", json_bytes(freeze_manifest))

    report = f"""# AppWorld test_normal-68 system-design-v3 updated-standard repair

This is a versioned, source-only refreeze of the 68 gpt-5.4/high drafts and a
global-contract repair of all 68 packets. It does not overwrite the earlier v6
assets or the system-design-v2 bundle.

## Frozen scope

- 68 `test_normal` cases
- {registered_test_count} released registered tests
- 68/68 case-specific draft checklists revalidated and byte-preserved from v2
- 68/68 packet contracts regenerated for the updated conflict/stronger policy
- stronger registry: {gap_case_count} gap cases, {68-gap_case_count} no-gap cases,
  {condition_count} conditions
- stronger content actions: {len(ACTION_CASE_IDS)} cases

## Updated-standard delta

The case-specific native tests and stronger conditions already met the updated
standard, so the checklist JSON/YAML bytes did not change. The v2 packets did,
however, encode released-label/native mismatch as a mandatory review entry and
used an over-broad `never establishes conflict` stronger sentence. Every packet
therefore carries a v3 global contract in which conflict review is independent:
mismatch is neither necessary nor sufficient, and neither stronger F alone nor
native S together with stronger F is sufficient to establish conflict.

## Boundary

The complete benchmark record and released label remain preserved outside the
scorer view.  A conforming scorer must use only allowlisted non-verdict evidence
and lock native S/F/U independently of the released result. Stronger conditions
are scored and reported independently. Confirmed benchmark conflict requires a
separate record-level audit with retained artifacts and explicit source pointers;
it is not gated by a released-label/native-verdict mismatch.

## Integration status

This bundle repairs and freezes the packets and drafts; it does not patch the
reference scoring runner, prompt, or conflict-audit workflow. The runner resolves
the released label before scoring and copies an evidence directory without the
allowlist; the prompt propagates native F/U into stronger F/U; and no AppWorld
record-level confirmed-conflict audit implements the source-pointer gate. These
assets must not be called end-to-end compliant until all four gates are implemented
and validated.
"""
    write_bytes(root / "README.md", report.encode("utf-8"))

    indexed_files = tree_index(root, omit={"repair_manifest.json"})
    repair_manifest = {
        "schema_version": "appworld_test_normal_68_repair_manifest.v2_standard_update",
        "created_date": GENERATED_DATE,
        "case_count": 68,
        "file_count_excluding_this_manifest": len(indexed_files),
        "files": indexed_files,
        "files_sha256": sha256_object(indexed_files),
        "validation": {
            "source_only_outcome_blind": True,
            "old_namespace_untouched": True,
            "packet_draft_exact_projection": True,
            "prior_standard_draft_bytes_preserved_case_count": 68,
            "updated_packet_contract_case_count": 68,
            "native_artifact_contract_case_count": 68,
            "native_explicit_sfu_case_count": 68,
            "stronger_counts": {
                "gap_cases": gap_case_count,
                "no_gap_cases": 68 - gap_case_count,
                "conditions": condition_count,
            },
        },
    }
    write_bytes(root / "repair_manifest.json", json_bytes(repair_manifest))
    return repair_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="rebuild in a temporary directory and compare with the existing output",
    )
    return parser.parse_args()


def require_isolated_output_root(output_root: Path) -> None:
    default_output_root = OUTPUT_ROOT.resolve()
    unsafe_exact = {
        Path("/").resolve(),
        Path.home().resolve(),
        REPO_ROOT.resolve(),
        (REPO_ROOT / "experiments").resolve(),
    }
    source_trees = {
        SOURCE_EXPERIMENT.resolve(),
        SOURCE_PACKET_ROOT.resolve(),
        SOURCE_DRAFT_ROOT.resolve(),
        FROZEN_EVALUATOR_SEMANTICS_SOURCE_TREE.resolve(),
        PRIOR_STANDARD_BUNDLE.resolve(),
    }
    if output_root in unsafe_exact:
        raise RuntimeError(f"unsafe broad output root: {output_root}")
    if output_root != default_output_root and (
        output_root in default_output_root.parents
        or default_output_root in output_root.parents
    ):
        raise RuntimeError(
            "custom output root must be disjoint from the default versioned output: "
            f"output={output_root}, default={default_output_root}"
        )
    for source in source_trees:
        if output_root == source or source in output_root.parents or output_root in source.parents:
            raise RuntimeError(
                "output root must be disjoint from every source/protected tree: "
                f"output={output_root}, protected={source}"
            )


def main() -> int:
    args = parse_args()
    output_root = args.output_root.expanduser().resolve()
    require_isolated_output_root(output_root)
    if args.check and not output_root.is_dir():
        raise RuntimeError(f"cannot check missing output root: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output_root.name}.tmp-", dir=output_root.parent
    ) as temporary:
        staged_root = Path(temporary) / output_root.name
        manifest = materialize(staged_root)
        if args.check:
            compare_trees(staged_root, output_root)
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "mode": "check",
                        "output_root": str(output_root),
                        "files_sha256": manifest["files_sha256"],
                    },
                    sort_keys=True,
                )
            )
            return 0
        if output_root.exists():
            raise RuntimeError(
                f"refusing to overwrite existing versioned output: {output_root}; "
                "use --check to validate it"
            )
        shutil.move(str(staged_root), str(output_root))
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": "build",
                "output_root": str(output_root),
                "files_sha256": manifest["files_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
