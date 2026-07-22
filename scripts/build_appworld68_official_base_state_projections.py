#!/usr/bin/env python3
"""Build outcome-blind AppWorld 0.2.0 base-state projections for conflict review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


RELATION_SINGULAR = {
    "children": "child",
    "coworkers": "coworker",
    "friends": "friend",
    "managers": "manager",
    "parents": "parent",
    "partners": "partner",
    "roommates": "roommate",
    "siblings": "sibling",
}
GROUP_KEY_RE = re.compile(r"(?:^|:)(\d+)$")


class ProjectionError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--base-dbs-root", type=Path, required=True)
    parser.add_argument("--case-id", action="append", default=[])
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def memory_copy(path: Path) -> sqlite3.Connection:
    source = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    destination = sqlite3.connect(":memory:")
    source.backup(destination)
    source.close()
    destination.row_factory = sqlite3.Row
    return destination


def apply_jsonl(connection: sqlite3.Connection, path: Path) -> None:
    if not path.is_file():
        raise ProjectionError(f"missing task-local database diff: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, list) or len(row) < 2:
            raise ProjectionError(f"malformed SQL row {path}:{line_number}")
        statement, parameters = row[0], row[1]
        connection.execute(statement, parameters)
    connection.commit()


def rows(connection: sqlite3.Connection, query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(query, parameters)]


def parse_relationships(value: Any) -> list[str]:
    if value is None:
        return []
    parsed = json.loads(value) if isinstance(value, str) else value
    if not isinstance(parsed, list):
        raise ProjectionError(f"contact relationships are not a list: {value!r}")
    return sorted(str(item) for item in parsed)


def collect_group_ids(value: Any) -> set[int]:
    found: set[int] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            match = GROUP_KEY_RE.search(str(key))
            if match and "group" in str(key).lower():
                found.add(int(match.group(1)))
            found.update(collect_group_ids(child))
        # AppWorld private mappings use group ids directly as keys beneath
        # group_id_to_* fields, so parse those child keys explicitly.
        for key, child in value.items():
            if str(key).startswith("group_id_to_") and isinstance(child, dict):
                for group_key in child:
                    match = GROUP_KEY_RE.search(str(group_key))
                    if match:
                        found.add(int(match.group(1)))
    elif isinstance(value, list):
        for child in value:
            found.update(collect_group_ids(child))
    return found


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def build_case_projection(
    workspace: Path,
    base_dbs_root: Path,
    base_lock: dict[str, Any],
) -> dict[str, Any] | None:
    specs = load_json(workspace / "official/specs.json")
    public_data = load_json(workspace / "official/ground_truth/public_data.json")
    requested_relation = public_data.get("relations") if isinstance(public_data, dict) else None
    if not isinstance(requested_relation, str):
        return None
    relation_token = RELATION_SINGULAR.get(requested_relation, requested_relation.rstrip("s"))
    supervisor = specs["supervisor"]

    phone = memory_copy(base_dbs_root / "phone.db")
    apply_jsonl(phone, workspace / "official/dbs/phone.jsonl")
    phone_users = rows(
        phone,
        "SELECT id, first_name, last_name, phone_number FROM users WHERE phone_number = ?",
        (supervisor["phone_number"],),
    )
    if len(phone_users) != 1:
        raise ProjectionError(f"cannot uniquely bind phone supervisor in {workspace.name}")
    phone_user = phone_users[0]
    contacts = rows(
        phone,
        """
        SELECT id, first_name, last_name, email, phone_number, relationships
        FROM contacts WHERE user_id = ? ORDER BY id
        """,
        (phone_user["id"],),
    )
    for contact in contacts:
        contact["relationships"] = parse_relationships(contact["relationships"])
    contacts_by_email = {str(contact["email"]).lower(): contact for contact in contacts}

    splitwise = memory_copy(base_dbs_root / "splitwise.db")
    base_group_max = splitwise.execute("SELECT COALESCE(MAX(id), 0) FROM groups").fetchone()[0]
    apply_jsonl(splitwise, workspace / "official/dbs/splitwise.jsonl")
    splitwise_supervisors = rows(
        splitwise,
        "SELECT id, first_name, last_name, email FROM users WHERE lower(email) = lower(?)",
        (supervisor["email"],),
    )
    if len(splitwise_supervisors) != 1:
        raise ProjectionError(f"cannot uniquely bind Splitwise supervisor in {workspace.name}")
    splitwise_supervisor = splitwise_supervisors[0]

    simple_note = memory_copy(base_dbs_root / "simple_note.db")
    base_note_max = simple_note.execute("SELECT COALESCE(MAX(id), 0) FROM notes").fetchone()[0]
    apply_jsonl(simple_note, workspace / "official/dbs/simple_note.jsonl")
    notes = rows(
        simple_note,
        "SELECT id, title, content FROM notes WHERE id > ? ORDER BY id",
        (base_note_max,),
    )
    note_by_title = {normalized_title(str(note["title"])): note for note in notes}

    private_data = load_json(workspace / "official/ground_truth/private_data.json")
    target_group_ids = collect_group_ids(private_data)
    added_groups = rows(
        splitwise,
        "SELECT id, name, description FROM groups WHERE id > ? ORDER BY id",
        (base_group_max,),
    )
    projected_groups: list[dict[str, Any]] = []
    for group in added_groups:
        members = rows(
            splitwise,
            """
            SELECT u.id, u.first_name, u.last_name, u.email
            FROM group_members gm JOIN users u ON u.id = gm.user_id
            WHERE gm.group_id = ? ORDER BY u.id
            """,
            (group["id"],),
        )
        non_supervisor: list[dict[str, Any]] = []
        for member in members:
            if int(member["id"]) == int(splitwise_supervisor["id"]):
                continue
            contact = contacts_by_email.get(str(member["email"]).lower())
            non_supervisor.append(
                {
                    **member,
                    "contact_relationships": None if contact is None else contact["relationships"],
                    "matches_requested_relation": bool(
                        contact is not None and relation_token in contact["relationships"]
                    ),
                }
            )
        note = note_by_title.get(normalized_title(str(group["name"])))
        projected_groups.append(
            {
                **group,
                "in_private_target": int(group["id"]) in target_group_ids,
                "all_non_supervisor_members_match_requested_relation": bool(non_supervisor)
                and all(member["matches_requested_relation"] for member in non_supervisor),
                "non_supervisor_members": non_supervisor,
                "matching_source_note": note,
            }
        )

    relation_matching_group_ids = sorted(
        int(group["id"])
        for group in projected_groups
        if group["all_non_supervisor_members_match_requested_relation"]
    )
    added_group_ids = sorted(int(group["id"]) for group in projected_groups)

    return {
        "schema_version": "appworld_official_base_state_relationship_projection/v1",
        "case_unit_id": workspace.name,
        "generation_phase": "official_source_only_before_record_outcome_review",
        "outcome_or_released_result_inputs_read": [],
        "data_version": base_lock["data_version"],
        "base_database_lock_sha256": base_lock["lock_sha256"],
        "instruction": specs["instruction"],
        "requested_relation_plural": requested_relation,
        "requested_relation_token": relation_token,
        "supervisor": {
            "specs": supervisor,
            "phone_user": phone_user,
            "splitwise_user": splitwise_supervisor,
        },
        "supervisor_contacts": contacts,
        "private_target_group_ids": sorted(target_group_ids),
        "relation_matching_added_group_ids": relation_matching_group_ids,
        "private_target_exactly_matches_relation_scope": sorted(target_group_ids)
        == relation_matching_group_ids,
        "all_task_added_group_ids": added_group_ids,
        "task_added_groups": projected_groups,
        "source_queries": {
            "phone_supervisor": "SELECT ... FROM users WHERE phone_number = specs.supervisor.phone_number",
            "phone_contacts": "SELECT ... FROM contacts WHERE user_id = bound_phone_supervisor.id",
            "splitwise_supervisor": "SELECT ... FROM users WHERE lower(email) = lower(specs.supervisor.email)",
            "task_groups": "apply official/dbs/splitwise.jsonl to official 0.2.0 splitwise.db; select groups added above the base max id",
            "task_notes": "apply official/dbs/simple_note.jsonl to official 0.2.0 simple_note.db; select notes added above the base max id",
        },
        "source_pointers": [
            "official/specs.json::$.instruction",
            "official/specs.json::$.supervisor",
            "official/ground_truth/public_data.json::$.relations",
            "official/ground_truth/private_data.json::$",
            "official/dbs/phone.jsonl::$",
            "official/dbs/simple_note.jsonl::$",
            "official/dbs/splitwise.jsonl::$",
            "official/base_state/base_database_lock.json::$",
        ],
    }


def main() -> int:
    args = parse_args()
    audit_root = args.audit_root.resolve()
    base_dbs_root = args.base_dbs_root.resolve()
    if (base_dbs_root / "version.txt").read_text(encoding="utf-8").strip() != "0.2.0":
        raise ProjectionError("base DB version is not exactly 0.2.0")
    database_paths = sorted(base_dbs_root.glob("*.db"))
    if not database_paths:
        raise ProjectionError("no official base databases found")
    base_lock_core = {
        "schema_version": "appworld_official_base_database_lock/v1",
        "authority": "official_appworld_data_0_2_0_bundle",
        "data_version": "0.2.0",
        "official_data_bundle_sha256": "c9299e6cafe92bce4592a3c117c047c973d1554a667c21dd81537e78ab2f532e",
        "database_sha256": {path.name: sha256_file(path) for path in database_paths},
        "outcome_or_released_result_inputs_read": [],
    }
    lock_bytes = json.dumps(base_lock_core, ensure_ascii=False, sort_keys=True).encode("utf-8")
    base_lock = {**base_lock_core, "lock_sha256": hashlib.sha256(lock_bytes).hexdigest()}

    index = load_json(audit_root / "index.json")
    requested = set(args.case_id)
    selected = [row for row in index if not requested or row["case_unit_id"] in requested]
    if requested and requested != {row["case_unit_id"] for row in selected}:
        raise ProjectionError("requested case selection differs from audit index")
    projected: list[str] = []
    for item in selected:
        workspace_value = Path(str(item["workspace"]))
        workspace = workspace_value if workspace_value.is_absolute() else audit_root / workspace_value
        projection = build_case_projection(workspace.resolve(), base_dbs_root, base_lock)
        if projection is None:
            continue
        output_dir = workspace / "official/base_state"
        write_json(output_dir / "base_database_lock.json", base_lock)
        write_json(output_dir / "relationship_scope.json", projection)
        projected.append(str(item["case_unit_id"]))
    write_json(
        audit_root / "official_base_state_projection_summary.json",
        {
            "schema_version": "appworld68_official_base_state_projection_summary/v1",
            "data_version": "0.2.0",
            "case_count": len(projected),
            "case_unit_ids": sorted(projected),
            "base_database_lock_sha256": base_lock["lock_sha256"],
            "outcome_or_released_result_inputs_read": [],
        },
    )
    print(json.dumps({"projected": len(projected), "case_unit_ids": sorted(projected)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
