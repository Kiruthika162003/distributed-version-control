from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.releasenotes import compose, cut
from keel.repo import Repo
from keel.tags import TagStore


def build() -> tuple[Repo, TagStore]:
    repo = Repo.init()
    first = repo.commit(
        {"app.py": b"core\n"}, "feat: the core"
    )
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", first.address, "first cut")
    repo.commit(
        {"app.py": b"core\nfast\n"},
        "fix: stop the slow path",
    )
    repo.commit(
        {"app.py": b"core\nfast\nrenamed\n"},
        "breaking: rename the entry point",
    )
    return repo, tags


class TestComposition:
    def test_the_three_claims_are_stapled(self):
        repo, tags = build()
        notes = compose(repo, tags, "v1.0", "v1.1")
        tip = repo.refs.current()
        assert notes.startswith(
            f"v1.1, cut at {tip[:8]}"
        )
        assert "the address is the release" in notes
        assert "Breaking changes, never buried" in notes
        assert "rename the entry point" in notes
        assert "stop the slow path" in notes
        assert "checksum: release" in notes
        assert (
            "where addresses cannot follow"
        ) in notes

    def test_a_release_of_nothing_is_refused(self):
        repo = Repo.init()
        first = repo.commit(
            {"app.py": b"core\n"}, "feat: the core"
        )
        tags = TagStore(graph=repo.graph)
        tags.place("v1.0", first.address, "first cut")
        with pytest.raises(Invalid) as caught:
            compose(repo, tags, "v1.0", "v1.1")
        assert "marketing's problem" in str(caught.value)

    def test_an_unknown_since_tag_is_refused(self):
        repo, tags = build()
        with pytest.raises(Missing):
            compose(repo, tags, "v0.9", "v1.1")


class TestTheCut:
    def test_the_document_and_seal_name_one_commit(self):
        repo, tags = build()
        notes, receipt = cut(
            repo, tags, "v1.0", "v1.1", "second cut"
        )
        tip = repo.refs.current()
        assert tip[:8] in notes
        assert tags.resolve("v1.1") == tip
        assert (
            "name the same commit by construction"
        ) in receipt

    def test_the_next_cycle_composes_from_the_new_seal(
        self,
    ):
        repo, tags = build()
        cut(repo, tags, "v1.0", "v1.1", "second cut")
        repo.commit(
            {"app.py": b"core\nfast\nrenamed\nmore\n"},
            "feat: one more",
        )
        notes = compose(repo, tags, "v1.1", "v1.2")
        assert "one more" in notes
        assert "stop the slow path" not in notes
