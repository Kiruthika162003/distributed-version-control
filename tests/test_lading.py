from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.lading import bill
from keel.push import PushGate
from keel.repo import Repo


def build() -> tuple[Repo, Repo, PushGate]:
    local = Repo.init()
    local.commit({"a.py": b"one\n"}, "first light")
    remote = Repo.init()
    gate = PushGate(remote=remote)
    gate.push(local, "main")
    local.commit(
        {"a.py": b"one\ntwo\n"}, "second thoughts"
    )
    local.commit(
        {"a.py": b"one\ntwo\nthree\n"}, "third rail"
    )
    return local, remote, gate


class TestTheBill:
    def test_the_freight_is_itemized_before_the_wire(
        self,
    ):
        local, remote, _gate = build()
        page = bill(local, remote, "main")
        assert page.startswith(
            "bill of lading for main: 6 object(s)"
        )
        assert "commit: 2" in page
        assert "tree: 2" in page
        assert "blob: 2" in page
        assert "shipping:" in page
        assert "third rail" in page
        assert "second thoughts" in page
        assert "never shown the bill" in page

    def test_quoting_moves_nothing(self):
        local, remote, _gate = build()
        before = len(remote.store.objects)
        bill(local, remote, "main")
        assert len(remote.store.objects) == before

    def test_the_bill_matches_the_shipment(self):
        local, remote, gate = build()
        page = bill(local, remote, "main")
        quoted = int(
            page.splitlines()[0].split(": ")[1].split(
                " object"
            )[0]
        )
        receipt = gate.push(local, "main")
        assert f"{quoted} object(s) shipped" in receipt
        after = bill(local, remote, "main")
        assert after.startswith("nothing to ship")

    def test_a_stranger_branch_is_refused(self):
        local, remote, _gate = build()
        with pytest.raises(Invalid):
            bill(local, remote, "ghost")
