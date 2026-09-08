from __future__ import annotations

from keel.binarydiff import compare, narrate


class TestMeasurements:
    def test_a_middle_edit_is_localized(self):
        old = b"HEADER" + b"old-core" + b"FOOTER"
        new = b"HEADER" + b"new!core" + b"FOOTER"
        delta = compare(old, new)
        assert delta.shared_head == 6
        assert delta.shared_tail == 10
        assert delta.old_core() == 4
        assert delta.new_core() == 4

    def test_containment_cannot_claim_bytes_twice(self):
        old = b"ABCD"
        new = b"ABCDABCD"
        delta = compare(old, new)
        assert (
            delta.shared_head + delta.shared_tail
            <= len(old)
        )
        assert delta.old_core() >= 0
        assert delta.new_core() >= 0

    def test_similarity_sorts_small_edits_above_rewrites(
        self,
    ):
        base = bytes(range(256)) * 4
        small_edit = (
            base[:500] + b"\x00\x00" + base[502:]
        )
        rewrite = bytes(
            (value + 128) % 256 for value in base
        )
        assert compare(base, small_edit).similarity() > (
            compare(base, rewrite).similarity()
        )


class TestNarration:
    def test_the_middle_is_where_the_story_hides(self):
        old = b"HEAD" + b"x" * 100 + b"TAIL"
        new = b"HEAD" + b"y" * 112 + b"TAIL"
        line = narrate("logo.png", old, new)
        assert line.startswith(
            "logo.png: 108 -> 120 byte(s) (+12)"
        )
        assert "4 shared at the head, 4 at the tail" in (
            line
        )
        assert "the middle 100 -> 112" in line
        assert "binaries do not tell stories" in line

    def test_identity_birth_and_emptying(self):
        assert narrate("a.bin", b"same", b"same") == (
            "a.bin: byte-identical; nothing moved"
        )
        assert narrate("a.bin", b"", b"12345") == (
            "a.bin: born at 5 byte(s)"
        )
        line = narrate("a.bin", b"12345", b"")
        assert line.startswith(
            "a.bin: emptied from 5 byte(s)"
        )
        assert "a deletion by another name" in line

    def test_shrinkage_carries_its_minus_sign(self):
        line = narrate(
            "a.bin", b"HEAD" + b"x" * 50, b"HEAD"
        )
        assert "(-50)" in line
