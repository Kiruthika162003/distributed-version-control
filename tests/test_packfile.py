from __future__ import annotations

import pytest

from keel.errors import Corrupt, Invalid
from keel.packfile import (
    Pack,
    apply_delta,
    delta_size,
    make_delta,
)

BASE = (
    b"def handler(request):\n"
    b"    validate(request)\n"
    b"    log(request)\n"
    b"    return respond(request)\n"
)
EDITED = (
    b"def handler(request):\n"
    b"    validate(request)\n"
    b"    audit(request)\n"
    b"    return respond(request)\n"
)


class TestDeltas:
    def test_the_delta_rebuilds_the_target_exactly(self):
        ops = make_delta(BASE, EDITED)
        assert apply_delta(BASE, ops) == EDITED

    def test_a_near_identical_edit_encodes_small(self):
        ops = make_delta(BASE, EDITED)
        assert delta_size(ops) < len(EDITED) // 2

    def test_the_copy_past_the_base_is_corrupt(self):
        ops = make_delta(BASE, EDITED)
        with pytest.raises(Corrupt) as caught:
            apply_delta(BASE[:10], ops)
        assert "disagree about history" in str(caught.value)


class TestThePack:
    def test_similar_blobs_ship_as_instructions(self):
        pack = Pack()
        base_address = pack.add(BASE)
        edited_address = pack.add(
            EDITED, base_address=base_address
        )
        assert edited_address in pack.deltas
        assert pack.restore(edited_address) == EDITED

    def test_the_unhelpful_delta_is_rejected_not_kept(self):
        pack = Pack()
        base_address = pack.add(b"a" * 40)
        stranger = pack.add(
            b"z" * 40, base_address=base_address
        )
        assert stranger in pack.full
        assert pack.rejected_deltas == 1

    def test_chains_are_bounded_by_depth(self):
        pack = Pack()
        previous = pack.add(BASE)
        payloads = [BASE]
        for round_number in range(5):
            edited = payloads[-1].replace(
                b"request", b"request" + bytes([65 + round_number]), 1
            )
            payloads.append(edited)
            previous = pack.add(edited, base_address=previous)
        depths = [
            pack._depth(address) for address in pack.deltas
        ]
        assert max(depths) <= 3

    def test_deltas_point_inward_never_out(self):
        pack = Pack()
        with pytest.raises(Invalid) as caught:
            pack.add(EDITED, base_address="feedface" * 3)
        assert "point inward, never out" in str(caught.value)

    def test_reconstruction_verifies_at_the_door(self):
        pack = Pack()
        base_address = pack.add(BASE)
        edited_address = pack.add(
            EDITED, base_address=base_address
        )
        pack.full[base_address] = BASE.replace(
            b"validate", b"corrupt!"
        )
        with pytest.raises(Corrupt):
            pack.restore(edited_address)

    def test_the_ledger_prices_the_pack_honestly(self):
        pack = Pack()
        base_address = pack.add(BASE)
        pack.add(EDITED, base_address=base_address)
        ledger = pack.ledger()
        assert "1 full object(s), 1 delta(s)" in ledger
        assert "byte(s) saved against the naive store" in ledger
