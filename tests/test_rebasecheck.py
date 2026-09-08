from __future__ import annotations

from keel.rebasecheck import narrate, verify
from keel.repo import Repo

BASE = {"a.py": b"base\n", "b.py": b"base\n"}


def build() -> tuple[Repo, str, str]:
    repo = Repo.init()
    root = repo.commit(dict(BASE), "root")
    old_one = repo.commit_with_parents(
        dict(BASE, **{"a.py": b"base\nwork\n"}),
        "work one",
        (root.address,),
    )
    old_tip = repo.commit_with_parents(
        dict(
            BASE,
            **{
                "a.py": b"base\nwork\n",
                "b.py": b"base\nmore\n",
            },
        ),
        "work two",
        (old_one.address,),
    )
    return repo, root.address, old_tip.address


class TestCleanRebases:
    def test_identical_trees_earn_the_receipt(self):
        repo, root, old_tip = build()
        new_one = repo.commit_with_parents(
            repo.files_at(old_tip),
            "work, replayed as one",
            (root,),
        )
        page = narrate(
            repo, old_tip, new_one.address, root
        )
        assert "content preserved to the byte" in page
        assert (
            "a receipt instead of a mood"
        ) in page
        assert "commits: 2 before, 1 after" in page
        assert "something folded on the way" in page


class TestDrift:
    def test_drift_is_reported_by_path_and_kind(self):
        repo, root, old_tip = build()
        drifted_files = dict(repo.files_at(old_tip))
        drifted_files["a.py"] = b"base\nWORK RESOLVED\n"
        del drifted_files["b.py"]
        drifted_files["c.py"] = b"fresh\n"
        new_tip = repo.commit_with_parents(
            drifted_files, "replayed with edits", (root,)
        )
        verdict = verify(
            repo, old_tip, new_tip.address, root
        )
        assert not verdict.clean
        assert verdict.drifted == (
            ("a.py", "edited"),
            ("b.py", "vanished"),
            ("c.py", "appeared"),
        )
        page = narrate(
            repo, old_tip, new_tip.address, root
        )
        assert "3 path(s) drifted" in page
        assert (
            "told what changed, not assured that "
            "nothing did"
        ) in page
