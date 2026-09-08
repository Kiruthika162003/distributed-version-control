from __future__ import annotations

from keel.freeze import FreezeBoard
from keel.quorum import QuorumLedger
from keel.repo import Repo
from keel.weighanchor import check

BASE = {"app.py": b"core\n"}


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    target = repo.commit(dict(BASE), "the target")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nmore\n"}),
        "downstream work",
    )
    return repo, target.address


def approved_ledger() -> QuorumLedger:
    ledger = QuorumLedger()
    ledger.propose("rewrite", "expunge the key", 2)
    ledger.approve("rewrite", "priya")
    ledger.approve("rewrite", "devi")
    return ledger


class TestTheChecklist:
    def test_clear_to_weigh_still_names_the_wake(self):
        repo, target = build()
        page = check(
            repo,
            target,
            proposal_key="rewrite",
            ledger=approved_ledger(),
        )
        assert (
            "1 commit(s) in the wake, 1 branch "
            "tip(s) riding"
        ) in page
        assert "CLEAR TO WEIGH" in page
        assert "permitted, not painless" in page

    def test_standing_orders_hold_the_anchor(self):
        repo, target = build()
        freezes = FreezeBoard()
        freezes.freeze("main", "cut week", "priya")
        page = check(
            repo,
            target,
            proposal_key="rewrite",
            ledger=approved_ledger(),
            freezes=freezes,
        )
        assert "HOLD FAST:" in page
        assert (
            "binds a rewrite exactly as it binds a "
            "landing"
        ) in page

    def test_a_short_quorum_holds_the_anchor(self):
        repo, target = build()
        ledger = QuorumLedger()
        ledger.propose("rewrite", "expunge", 3)
        ledger.approve("rewrite", "priya")
        page = check(
            repo,
            target,
            proposal_key="rewrite",
            ledger=ledger,
        )
        assert "HOLD FAST:" in page
        assert (
            "rewrite stands at 1 of 3; short of "
            "quorum"
        ) in page

    def test_the_unproposed_rewrite_writes_its_report(
        self,
    ):
        repo, target = build()
        page = check(
            repo,
            target,
            proposal_key="rewrite",
            ledger=QuorumLedger(),
        )
        assert (
            "writes its own incident report"
        ) in page
