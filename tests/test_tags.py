from __future__ import annotations

import pytest

from keel.commits import CommitGraph
from keel.errors import Invalid, Missing
from keel.objects import TREE, ObjectStore
from keel.tags import TagStore


def stack() -> tuple[TagStore, list[str]]:
    graph = CommitGraph(store=ObjectStore())
    addresses = []
    parent: tuple[str, ...] = ()
    for number in range(4):
        tree = graph.store.put(TREE, f"t{number}".encode())
        commit = graph.create(tree, parent, f"c{number}")
        addresses.append(commit.address)
        parent = (commit.address,)
    return TagStore(graph=graph), addresses


class TestPlacing:
    def test_a_tag_seals_bytes_not_a_moment(self):
        tags, line = stack()
        tags.place("v1.0", line[1], "first release")
        assert tags.resolve("v1.0") == line[1]
        with pytest.raises(Invalid) as caught:
            tags.place("v1.0", line[2], "oops")
        assert "about a moment instead of about bytes" in str(
            caught.value
        )

    def test_the_message_is_not_optional(self):
        tags, line = stack()
        with pytest.raises(Invalid) as caught:
            tags.place("v1.0", line[0], "  ")
        assert "a bookmark wearing a suit" in str(caught.value)

    def test_the_target_must_exist(self):
        tags, _ = stack()
        with pytest.raises(Missing):
            tags.place("v1.0", "feedfacefeedfacefeed", "ghost")

    def test_names_are_one_word(self):
        tags, line = stack()
        with pytest.raises(Invalid):
            tags.place("v 1", line[0], "spaced")


class TestLookup:
    def test_listing_sorts_because_lookup_wants_order(self):
        tags, line = stack()
        tags.place("v2.0", line[3], "second")
        tags.place("v1.0", line[1], "first")
        listing = tags.listing()
        assert listing[0].startswith("v1.0 -> ")
        assert listing[1].startswith("v2.0 -> ")

    def test_describe_names_the_nearest_tag_below(self):
        tags, line = stack()
        tags.place("v1.0", line[1], "first")
        assert tags.describe(line[1]) == "exactly v1.0"
        assert tags.describe(line[3]) == "v1.0 plus 2 commit(s)"
        assert tags.describe(line[0]) == (
            "no tag reaches this commit"
        )


class TestDeletion:
    def test_deletion_is_journaled_with_the_abandoned_address(self):
        tags, line = stack()
        tags.place("rc1", line[2], "candidate")
        verdict = tags.delete("rc1")
        assert "keeps the address it abandoned" in verdict
        assert any(
            "abandoning" in entry for entry in tags.journal
        )
        with pytest.raises(Missing):
            tags.resolve("rc1")
