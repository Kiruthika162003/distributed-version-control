from __future__ import annotations

import pytest

from keel.errors import Corrupt, Invalid, Missing
from keel.largefiles import (
    Intake,
    Warehouse,
    is_pointer,
    make_pointer,
    parse_pointer,
)

BIG = b"x" * 10_001
NEAR = b"y" * 9_500
SMALL = b"z" * 100


def intake() -> Intake:
    return Intake(warehouse=Warehouse())


class TestPointers:
    def test_the_card_carries_digest_and_size(self):
        pointer = make_pointer(BIG)
        digest, size = parse_pointer(pointer)
        assert size == 10_001
        assert len(digest) == 20
        assert is_pointer(pointer)

    def test_ordinary_content_is_not_a_pointer(self):
        assert not is_pointer(SMALL)
        with pytest.raises(Invalid):
            parse_pointer(SMALL)


class TestIntake:
    def test_the_big_file_is_crated(self):
        desk = intake()
        stored, receipt = desk.admit("data.bin", BIG)
        assert is_pointer(stored)
        assert "history keeps the business card" in receipt
        assert desk.pointered == 1

    def test_the_near_miss_is_named_not_hidden(self):
        desk = intake()
        stored, receipt = desk.admit("close.bin", NEAR)
        assert stored == NEAR
        assert "500 under the line" in receipt
        assert "breed folklore" in receipt
        assert desk.near_misses == ["close.bin"]

    def test_the_small_file_passes_quietly(self):
        desk = intake()
        stored, receipt = desk.admit("tiny.txt", SMALL)
        assert stored == SMALL
        assert receipt == "tiny.txt: admitted whole"


class TestMaterializing:
    def test_the_crate_round_trips(self):
        desk = intake()
        stored, _ = desk.admit("data.bin", BIG)
        assert desk.materialize("data.bin", stored) == BIG
        assert desk.warehouse.fetches == 1

    def test_the_missing_crate_names_path_and_digest(self):
        desk = intake()
        stored, _ = desk.admit("data.bin", BIG)
        desk.warehouse.crates.clear()
        with pytest.raises(Missing) as caught:
            desk.materialize("data.bin", stored)
        assert "data.bin points at" in str(caught.value)
        assert "exactly what is missing" in str(caught.value)

    def test_the_mislabeled_crate_is_corrupt(self):
        desk = intake()
        stored, _ = desk.admit("data.bin", BIG)
        digest, _ = parse_pointer(stored)
        desk.warehouse.crates[digest] = b"swapped contents"
        with pytest.raises(Corrupt):
            desk.materialize("data.bin", stored)
