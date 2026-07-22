from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidence_system.contracts.appworld_support_pointers import (
    canonical_archive_path,
    official_pointer_resolves,
    support_location_resolves,
)


def test_json_pointer_dialect_accepts_root_object_and_root_list(tmp_path: Path) -> None:
    object_path = tmp_path / "object.json"
    list_path = tmp_path / "list.json"
    object_path.write_text(json.dumps({"outer": {"items": [{"value": 7}]}}))
    list_path.write_text(json.dumps([{"value": 7}]))

    assert support_location_resolves(object_path, "$")
    assert support_location_resolves(object_path, "$.outer.items[0].value")
    assert support_location_resolves(list_path, "$[0].value")
    assert not support_location_resolves(object_path, "root")
    assert not support_location_resolves(object_path, "$.outer.items[1]")
    assert not support_location_resolves(list_path, "$[00].value")
    assert not support_location_resolves(object_path, "$ ")
    assert not support_location_resolves(object_path, " $.outer")


def test_python_symbol_must_be_a_unique_ast_definition(tmp_path: Path) -> None:
    valid = tmp_path / "valid.py"
    duplicate = tmp_path / "duplicate.py"
    comment_only = tmp_path / "comment.py"
    valid.write_text("def evaluate():\n    return 1\n", encoding="utf-8")
    duplicate.write_text(
        "def evaluate():\n    return 1\ndef evaluate():\n    return 2\n",
        encoding="utf-8",
    )
    comment_only.write_text("# evaluate\nvalue = 'evaluate'\n", encoding="utf-8")

    assert support_location_resolves(valid, "evaluate")
    assert not support_location_resolves(duplicate, "evaluate")
    assert not support_location_resolves(comment_only, "evaluate")


@pytest.mark.parametrize(
    "source,symbol",
    [
        (
            "def evaluate():\n    return 1\nif FLAG:\n    def evaluate():\n        return 2\n",
            "evaluate",
        ),
        (
            "def evaluate():\n    return 1\ntry:\n    pass\nexcept:\n    def evaluate():\n        return 2\n",
            "evaluate",
        ),
        (
            "class C:\n    def evaluate(self):\n        return 1\n    if FLAG:\n        def evaluate(self):\n            return 2\n",
            "C.evaluate",
        ),
    ],
)
def test_python_symbol_rejects_control_flow_hidden_duplicates(
    tmp_path: Path, source: str, symbol: str
) -> None:
    path = tmp_path / "hidden.py"
    path.write_text(source, encoding="utf-8")
    assert not support_location_resolves(path, symbol)


def test_official_pointer_rejects_traversal_off_inventory_and_symlink(
    tmp_path: Path,
) -> None:
    task_dir = tmp_path / "task"
    official = task_dir / "ground_truth"
    official.mkdir(parents=True)
    evaluation = official / "evaluation.py"
    evaluation.write_text("def evaluate():\n    return 1\n", encoding="utf-8")
    inventory = {"official/ground_truth/evaluation.py"}

    assert official_pointer_resolves(
        task_dir=task_dir,
        pointer="official/ground_truth/evaluation.py::evaluate",
        inventory_paths=inventory,
    )
    for pointer in (
        "official/../ground_truth/evaluation.py::evaluate",
        "official/ground_truth/evaluation.py::evaluate ",
        "official/specs.json::$",
        "/official/ground_truth/evaluation.py::evaluate",
    ):
        assert not official_pointer_resolves(
            task_dir=task_dir,
            pointer=pointer,
            inventory_paths=inventory,
        )

    link = official / "linked.py"
    try:
        link.symlink_to(evaluation)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    assert not official_pointer_resolves(
        task_dir=task_dir,
        pointer="official/ground_truth/linked.py::evaluate",
        inventory_paths={"official/ground_truth/linked.py"},
    )


@pytest.mark.parametrize(
    "value",
    [
        "/official/specs.json",
        "./official/specs.json",
        "official/../specs.json",
        "official//specs.json",
        "official\\specs.json",
    ],
)
def test_archive_path_must_be_canonical(value: str) -> None:
    assert canonical_archive_path(value) is None
