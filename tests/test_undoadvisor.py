from __future__ import annotations

import pytest

from keel.errors import Missing
from keel.repo import Repo
from keel.undoadvisor import UndoAdvisor


def build() -> tuple[Repo, UndoAdvisor]:
    repo = Repo.init()
    repo.commit({"app.py": b"one\n"}, "first")
    repo.commit({"app.py": b"one\ntwo\n"}, "second")
    return repo, UndoAdvisor(repo=repo)


class TestDeletedBranches:
    def test_the_advice_carries_all_three_parts(self):
        repo, advisor = build()
        repo.branch_from_head("doomed")
        repo.refs.delete("doomed")
        advice = advisor.deleted_branch("doomed")
        assert "removed the name, not the history" in (
            advice.diagnosis
        )
        assert advice.evidence.startswith(
            "branch doomed deleted at"
        )
        assert "point a branch at" in advice.prescription
        rendered = advice.render()
        assert "diagnosis:" in rendered
        assert "prescription:" in rendered

    def test_resurrection_restores_the_exact_tip(self):
        repo, advisor = build()
        repo.branch_from_head("doomed")
        tip = repo.refs.branches["doomed"]
        repo.refs.delete("doomed")
        receipt = advisor.resurrect("doomed")
        assert "stands again" in receipt
        assert repo.refs.branches["doomed"] == tip

    def test_an_unrecorded_deletion_is_an_honest_refusal(
        self,
    ):
        _repo, advisor = build()
        with pytest.raises(Missing) as caught:
            advisor.deleted_branch("never-existed")
        assert "not every loss is recoverable" in str(
            caught.value
        )


class TestResetVictims:
    def test_the_abandoned_tip_is_diagnosed(self):
        repo, advisor = build()
        old_tip = repo.refs.current()
        first = repo.graph.log(old_tip)[-1]
        repo.refs.move(
            "main",
            first.address,
            reason="oops reset",
            force=True,
        )
        advice = advisor.reset_victim("main")
        assert old_tip[:8] in advice.diagnosis
        assert "oops reset" in advice.diagnosis
        assert "before the journal is trimmed" in (
            advice.prescription
        )

    def test_the_rescue_branch_holds_the_abandoned_work(
        self,
    ):
        repo, advisor = build()
        old_tip = repo.refs.current()
        first = repo.graph.log(old_tip)[-1]
        repo.refs.move(
            "main",
            first.address,
            reason="oops reset",
            force=True,
        )
        receipt = advisor.rescue("main", "rescued")
        assert "can no longer take it" in receipt
        assert repo.refs.branches["rescued"] == old_tip

    def test_a_branch_never_reset_gets_the_truth(self):
        _repo, advisor = build()
        with pytest.raises(Missing) as caught:
            advisor.reset_victim("main")
        assert "not a reset this repository saw" in str(
            caught.value
        )
