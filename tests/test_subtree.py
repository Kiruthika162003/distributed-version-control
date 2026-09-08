from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid, Missing
from keel.repo import Repo
from keel.subtree import SubtreeLedger


def build() -> tuple[Repo, Repo, SubtreeLedger]:
    host = Repo.init()
    host.commit({"app.py": b"host core\n"}, "host base")
    guest = Repo.init()
    guest.commit(
        {"parse.py": b"parse v1\n", "emit.py": b"emit v1\n"},
        "guest base",
    )
    return host, guest, SubtreeLedger(host=host)


class TestGrafting:
    def test_the_graft_lands_prefixed_and_sourced(self):
        host, guest, ledger = build()
        receipt = ledger.add(guest, "vendor/parser/")
        assert receipt.startswith(
            "grafted 2 file(s) under vendor/parser/"
        )
        files = host.head_files()
        assert files["vendor/parser/parse.py"] == (
            b"parse v1\n"
        )
        assert files["app.py"] == b"host core\n"

    def test_a_prefix_without_a_slash_is_refused(self):
        _host, guest, ledger = build()
        with pytest.raises(Invalid):
            ledger.add(guest, "vendor/parser")

    def test_occupied_ground_is_refused(self):
        host, guest, ledger = build()
        host.commit(
            {
                "app.py": b"host core\n",
                "vendor/parser/old.py": b"squatter\n",
            },
            "host squats",
        )
        with pytest.raises(Invalid) as caught:
            ledger.add(guest, "vendor/parser/")
        assert "buries somebody's work" in str(caught.value)

    def test_overlapping_grafts_are_refused(self):
        _host, guest, ledger = build()
        ledger.add(guest, "vendor/parser/")
        other = Repo.init()
        other.commit({"x.py": b"x\n"}, "other base")
        with pytest.raises(Invalid) as caught:
            ledger.add(other, "vendor/parser/deep/")
        assert "org chart, not a tree" in str(caught.value)


class TestPulling:
    def test_upstream_changes_arrive_and_move_the_record(
        self,
    ):
        host, guest, ledger = build()
        ledger.add(guest, "vendor/parser/")
        guest.commit(
            {
                "parse.py": b"parse v2\n",
                "emit.py": b"emit v1\n",
            },
            "guest improves parse",
        )
        receipt = ledger.pull(guest, "vendor/parser/")
        assert receipt.startswith("pulled 1 change(s)")
        assert host.head_files()[
            "vendor/parser/parse.py"
        ] == b"parse v2\n"

    def test_a_current_graft_pulls_nothing(self):
        _host, guest, ledger = build()
        ledger.add(guest, "vendor/parser/")
        receipt = ledger.pull(guest, "vendor/parser/")
        assert "nothing upstream moved" in receipt

    def test_a_local_fork_is_named_not_erased(self):
        host, guest, ledger = build()
        ledger.add(guest, "vendor/parser/")
        files = dict(host.head_files())
        files["vendor/parser/parse.py"] = (
            b"parse v1\nlocal patch\n"
        )
        host.commit(files, "host patches the vendored file")
        guest.commit(
            {
                "parse.py": b"parse v2\n",
                "emit.py": b"emit v1\n",
            },
            "guest improves parse",
        )
        with pytest.raises(Conflict) as caught:
            ledger.pull(guest, "vendor/parser/")
        message = str(caught.value)
        assert "vendor/parser/parse.py" in message
        assert "erase the fork silently" in message

    def test_pulling_an_ungrafted_prefix_is_refused(self):
        _host, guest, ledger = build()
        with pytest.raises(Missing):
            ledger.pull(guest, "vendor/parser/")

    def test_upstream_deletions_arrive_too(self):
        host, guest, ledger = build()
        ledger.add(guest, "vendor/parser/")
        guest.commit(
            {"parse.py": b"parse v1\n"}, "guest drops emit"
        )
        ledger.pull(guest, "vendor/parser/")
        assert (
            "vendor/parser/emit.py"
            not in host.head_files()
        )


class TestSplitting:
    def test_the_reverse_door_hands_back_plain_files(self):
        _host, guest, ledger = build()
        ledger.add(guest, "vendor/parser/")
        stripped, receipt = ledger.split("vendor/parser/")
        assert stripped == {
            "parse.py": b"parse v1\n",
            "emit.py": b"emit v1\n",
        }
        assert "the reverse door stays oiled" in receipt

    def test_splitting_an_ungrafted_prefix_is_refused(
        self,
    ):
        _host, _guest, ledger = build()
        with pytest.raises(Missing):
            ledger.split("vendor/parser/")
