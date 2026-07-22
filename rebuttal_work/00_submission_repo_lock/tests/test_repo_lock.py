from __future__ import annotations

import hashlib
import json
import stat
import unittest
from pathlib import Path


LOCK_DIR = Path(__file__).resolve().parents[1]
ROOT = LOCK_DIR.parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class RepoLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = json.loads((LOCK_DIR / "submission_repo_lock.json").read_text(encoding="utf-8"))

    def test_commit_tree_and_archive(self) -> None:
        repository = self.lock["submission_repository"]
        self.assertEqual(repository["commit"], "ffd9ff4e706d85ff2d12e60f087cde664dbae433")
        self.assertEqual(repository["commit_tree_oid"], "9339be9873fca806a2e77ffe724f11c61fcbfd80")
        self.assertEqual(
            self.lock["archives"]["full_git_archive"]["sha256"],
            "6fc564e106ba92317c931427cdab759070296857e3d1a22347bbb682ac156ea5",
        )
        archive = LOCK_DIR / "submission_source_archive.tar"
        self.assertEqual(sha256(archive), self.lock["archives"]["minimal_source_archive"]["sha256"])

    def test_dependency_and_repo_state_locks(self) -> None:
        self.assertTrue(self.lock["dependencies"]["exact_lock_present"])
        self.assertEqual(self.lock["submodules"]["gitlink_count"], 0)
        self.assertFalse(self.lock["large_files"]["lfs_rules_present_at_submission"])
        diff = json.loads((LOCK_DIR / "repo_diff_index.json").read_text(encoding="utf-8"))
        self.assertGreater(diff["legacy_worktree_untracked_count_excluding_step1_outputs"], 0)
        self.assertFalse(self.lock["legacy_repository"]["working_tree_clean_claim"])
        legacy = self.lock["legacy_repository"]
        self.assertTrue(legacy["filesystem_immutable_all_entries_verified"])
        self.assertEqual(
            {entry["path"] for entry in legacy["filesystem_immutable_roots"]},
            {"neurips_ed_track_minimal", "results", "paper_result_packages"},
        )
        immutable = getattr(stat, "UF_IMMUTABLE", 0)
        self.assertNotEqual(immutable, 0)
        for entry in legacy["filesystem_immutable_roots"]:
            self.assertTrue((ROOT / entry["path"]).stat().st_flags & immutable)

    def test_snapshots_are_read_only(self) -> None:
        for name in ("SUBMISSION_REPO", "LEGACY_HEAD_SNAPSHOT"):
            root = LOCK_DIR / "snapshots" / name
            writable = []
            for path in [root, *root.rglob("*")]:
                if path.lstat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
                    writable.append(path)
            self.assertEqual(writable, [], name)

    def test_output_root_is_disjoint(self) -> None:
        output = ROOT / self.lock["submission_repository"]["new_execution_output_root"]
        submission = LOCK_DIR / "snapshots/SUBMISSION_REPO"
        legacy = LOCK_DIR / "snapshots/LEGACY_HEAD_SNAPSHOT"
        self.assertNotIn(submission.resolve(), output.resolve().parents)
        self.assertNotIn(legacy.resolve(), output.resolve().parents)


if __name__ == "__main__":
    unittest.main()
