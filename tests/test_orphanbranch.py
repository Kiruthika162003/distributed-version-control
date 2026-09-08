from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid, Missing
from keel.orphanbranch import (
    adopt,
    are_strangers,
    create_orphan,
)
from keel.repo import Repo


def build() -> Repo:
    repo = Repo.init()
    repo.commit({"app.py": b"core\n"}, "main base")
    repo.commit({"app.py": b"core\nmore\n"}, "main grows")
    return repo


class TestCreation:
    def test_the_orphan_has_no_parents_and_a_branch(self):
        repo = build()
        commit = create_orphan(
            repo,
            "site",
            {"index.html": b"<h1>docs</h1>\n"},
            "site root",
        )
        assert commit.parents == ()
        assert repo.refs.branches["site"] == commit.address

    def test_a_taken_name_is_refused(self):
        repo = build()
        with pytest.raises(Invalid) as caught:
            create_orphan(
                repo, "main", {"x": b"x\n"}, "impostor"
            )
        assert "nobody answers to" in str(caught.value)

    def test_a_bodiless_orphan_is_refused(self):
        repo = build()
        with pytest.raises(Invalid):
            create_orphan(repo, "site", {}, "empty")

    def test_the_histories_are_strangers_by_construction(
        self,
    ):
        repo = build()
        commit = create_orphan(
            repo, "site", {"index.html": b"hi\n"}, "root"
        )
        assert are_strangers(
            repo,
            repo.refs.branches["main"],
            commit.address,
        )
        with pytest.raises(Missing) as caught:
            repo.graph.merge_base(
                repo.refs.branches["main"], commit.address
            )
        assert "strangers, not branches" in str(
            caught.value
        )


class TestAdoption:
    def test_disjoint_strangers_marry_into_a_union(self):
        repo = build()
        create_orphan(
            repo, "site", {"index.html": b"hi\n"}, "root"
        )
        merged = adopt(
            repo, "main", "site", "adopt the site"
        )
        assert len(merged.parents) == 2
        files = repo.files_at(merged.address)
        assert files["app.py"] == b"core\nmore\n"
        assert files["index.html"] == b"hi\n"
        assert repo.refs.branches["main"] == merged.address

    def test_contested_paths_are_listed_all_at_once(self):
        repo = build()
        create_orphan(
            repo,
            "site",
            {
                "app.py": b"impostor\n",
                "README": b"other readme\n",
            },
            "root",
        )
        main_files = repo.head_files()
        repo.commit(
            {**main_files, "README": b"main readme\n"},
            "main adds readme",
        )
        with pytest.raises(Conflict) as caught:
            adopt(repo, "main", "site", "adopt the site")
        message = str(caught.value)
        assert "2 path(s) contested" in message
        assert "README" in message
        assert "app.py" in message
        assert "coin flip wearing a robe" in message

    def test_relatives_are_sent_to_the_front_door(self):
        repo = build()
        repo.branch_from_head("feature")
        with pytest.raises(Invalid) as caught:
            adopt(repo, "main", "feature", "adopt kin")
        assert "front door" in str(caught.value)

    def test_adoption_needs_both_branches(self):
        repo = build()
        with pytest.raises(Invalid):
            adopt(repo, "main", "ghost", "adopt a ghost")
