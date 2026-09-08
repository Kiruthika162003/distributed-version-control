from __future__ import annotations

import pytest

from keel.commits import CommitGraph
from keel.errors import Invalid, Missing
from keel.notes import NoteSpace
from keel.objects import TREE, ObjectStore


def noted() -> tuple[NoteSpace, str]:
    graph = CommitGraph(store=ObjectStore())
    tree = graph.store.put(TREE, b"t")
    commit = graph.create(tree, (), "the commit")
    return NoteSpace(graph=graph), commit.address


class TestAttaching:
    def test_the_address_does_not_move(self):
        notes, address = noted()
        verdict = notes.attach(
            "ci", address, "build green in 41s"
        )
        assert "the commit's address did not move" in verdict
        assert notes.read("ci", address) == (
            "build green in 41s"
        )

    def test_amending_is_named_as_amending(self):
        notes, address = noted()
        notes.attach("ci", address, "first run")
        verdict = notes.attach("ci", address, "second run")
        assert "amended" in verdict
        assert notes.read("ci", address) == "second run"

    def test_namespaces_are_one_word_channels(self):
        notes, address = noted()
        with pytest.raises(Invalid):
            notes.attach("ci/results", address, "x")

    def test_empty_notes_are_nudges(self):
        notes, address = noted()
        with pytest.raises(Invalid):
            notes.attach("ci", address, "  ")

    def test_notes_need_a_real_commit(self):
        notes, _ = noted()
        with pytest.raises(Missing):
            notes.attach("ci", "feedfacefeedfacefeed", "x")


class TestLifecycle:
    def test_removal_states_the_philosophy(self):
        notes, address = noted()
        notes.attach("review", address, "approved")
        verdict = notes.remove("review", address)
        assert "different lifecycle rules than facts" in verdict
        with pytest.raises(Missing):
            notes.read("review", address)

    def test_the_render_labels_every_opinion(self):
        notes, address = noted()
        notes.attach("ci", address, "green")
        notes.attach("review", address, "two approvals")
        page = notes.render(address)
        assert "[ci] green" in page
        assert "[review] two approvals" in page

    def test_the_bare_commit_stands_alone(self):
        notes, address = noted()
        assert "the commit stands alone" in notes.render(
            address
        )
