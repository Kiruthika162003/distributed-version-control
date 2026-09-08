from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.frontier import last_accord, report
from keel.repo import Repo

BASE = {"app.py": b"core\n"}


def fleet() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit(dict(BASE), "founding")
    accord = repo.commit(
        dict(BASE, **{"app.py": b"core\nshared\n"}),
        "the accord",
    )
    for name, extra in (
        ("east", 1),
        ("west", 3),
    ):
        repo.refs.checkout("main")
        repo.branch_from_head(name)
        repo.refs.checkout(name)
        text = b"core\nshared\n"
        for step in range(extra):
            text += f"{name}{step}\n".encode()
            repo.commit(
                dict(BASE, **{"app.py": text}),
                f"{name} step {step}",
            )
    repo.refs.checkout("main")
    return repo, accord.address


class TestTheAccord:
    def test_the_newest_shared_commit_is_found(self):
        repo, accord = fleet()
        assert last_accord(
            repo, ["main", "east", "west"]
        ) == accord

    def test_distances_sort_farthest_first(self):
        repo, _accord = fleet()
        page = report(repo, ["main", "east", "west"])
        assert page.startswith(
            "the last accord:"
        )
        assert "'the accord'" in page
        lines = page.splitlines()
        assert lines[1] == "  west: 3 commit(s) out"
        assert lines[2] == "  east: 1 commit(s) out"
        assert lines[3] == "  main: still at the accord"
        assert (
            "west sails farthest"
        ) in page

    def test_one_ship_is_not_a_fleet(self):
        repo, _accord = fleet()
        with pytest.raises(Invalid):
            report(repo, ["main"])


class TestSquadrons:
    def test_strangers_are_squadrons_not_a_fleet(self):
        repo, _accord = fleet()
        stray = repo.graph.create(
            tree=repo.snapshot_tree(
                {"island.txt": b"alone\n"}
            ),
            parents=(),
            message="island root",
        )
        repo.refs.create_branch("island", stray.address)
        page = report(
            repo, ["main", "east", "island"]
        )
        assert page.startswith(
            "not a fleet but 2 squadron(s):"
        )
        assert "east, main" in page
        assert "island" in page
        assert (
            "a reunion nobody can attend"
        ) in page
