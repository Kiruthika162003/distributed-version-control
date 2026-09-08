from __future__ import annotations

import pytest

from keel.errors import Corrupt, Invalid, Missing
from keel.objects import BLOB, TREE, ObjectStore, digest_bytes


def store() -> ObjectStore:
    return ObjectStore()


class TestAddressing:
    def test_content_is_its_own_address(self):
        chosen = store()
        address = chosen.put(BLOB, b"hello")
        assert address == digest_bytes(BLOB, b"hello")
        assert chosen.get(address) == b"hello"

    def test_kind_is_part_of_the_address(self):
        assert digest_bytes(BLOB, b"x") != digest_bytes(
            TREE, b"x"
        )

    def test_identical_content_stores_once(self):
        chosen = store()
        first = chosen.put(BLOB, b"shared")
        second = chosen.put(BLOB, b"shared")
        assert first == second
        assert chosen.writes == 1
        assert chosen.dedup_hits == 1

    def test_the_menu_of_kinds_is_closed(self):
        with pytest.raises(Invalid) as caught:
            store().put("wish", b"x")
        assert "the menu is" in str(caught.value)


class TestTheTwoDoors:
    def test_the_read_side_check_catches_tampering(self):
        chosen = store()
        address = chosen.put(BLOB, b"honest")
        kind, _ = chosen.objects[address]
        chosen.objects[address] = (kind, b"tampered")
        with pytest.raises(Corrupt) as caught:
            chosen.get(address)
        assert "worse than a dead one" in str(caught.value)

    def test_kind_expectations_are_enforced(self):
        chosen = store()
        address = chosen.put(BLOB, b"x")
        with pytest.raises(Invalid) as caught:
            chosen.get(address, expect=TREE)
        assert "addresses do not lie about kind" in str(
            caught.value
        )

    def test_the_stale_address_is_named(self):
        with pytest.raises(Missing) as caught:
            store().get("feedfacefeedfacefeed")
        assert "stale address" in str(caught.value)


class TestTheLedger:
    def test_dedup_is_counted_not_assumed(self):
        chosen = store()
        chosen.put(BLOB, b"a")
        chosen.put(BLOB, b"a")
        chosen.put(BLOB, b"b")
        assert chosen.ledger() == (
            "2 object(s) stored, 1 duplicate write(s) "
            "collapsed by content addressing"
        )

    def test_kind_of_answers_without_payload(self):
        chosen = store()
        address = chosen.put(TREE, b"shape")
        assert chosen.kind_of(address) == TREE
