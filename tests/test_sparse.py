from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.sparse import SparseDesk

MONOREPO = {
    "team-a/app.py": b"a code",
    "team-a/util.py": b"a util",
    "team-b/service.py": b"b code",
    "shared/lib.py": b"shared",
}


def desk() -> SparseDesk:
    repo = Repo.init()
    repo.commit(dict(MONOREPO), "monorepo base")
    built = SparseDesk(repo=repo)
    built.widen("team-a")
    return built


class TestTheProfile:
    def test_only_the_corner_materializes(self):
        chosen = desk()
        files = chosen.materialize()
        assert sorted(files) == [
            "team-a/app.py", "team-a/util.py",
        ]
        assert "2 of 4 file(s) on the desk" in (
            chosen.coverage()
        )

    def test_widening_is_additive(self):
        chosen = desk()
        chosen.widen("shared/")
        assert len(chosen.materialize()) == 3

    def test_the_empty_profile_materializes_nothing(self):
        repo = Repo.init()
        repo.commit(dict(MONOREPO), "base")
        with pytest.raises(Invalid):
            SparseDesk(repo=repo).materialize()


class TestTheEdges:
    def test_hidden_is_never_not_found(self):
        chosen = desk()
        with pytest.raises(Missing) as caught:
            chosen.read("team-b/service.py")
        assert "outside the sparse profile" in str(caught.value)
        assert "must never read as not-found" in str(
            caught.value
        )
        with pytest.raises(Missing) as caught:
            chosen.read("ghost.py")
        assert "is not in HEAD" in str(caught.value)

    def test_a_sparse_commit_preserves_the_unseen_world(self):
        chosen = desk()
        commit = chosen.commit_sparse(
            {"team-a/app.py": b"a code v2"},
            "edit inside the corner",
        )
        files = chosen.repo.files_at(commit.address)
        assert files["team-a/app.py"] == b"a code v2"
        assert files["team-b/service.py"] == b"b code"
        assert "team-a/util.py" not in files

    def test_the_desk_cannot_speak_for_hidden_paths(self):
        chosen = desk()
        with pytest.raises(Invalid) as caught:
            chosen.commit_sparse(
                {"team-b/service.py": b"sneaky"},
                "outside edit",
            )
        assert "directories it does not show" in str(
            caught.value
        )
