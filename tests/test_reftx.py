from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.reftx import RefTransaction
from keel.repo import Repo


def build() -> tuple[Repo, list[str]]:
    repo = Repo.init()
    first = repo.commit({"a.py": b"1\n"}, "one")
    second = repo.commit({"a.py": b"1\n2\n"}, "two")
    repo.branch_from_head("feature")
    return repo, [first.address, second.address]


class TestValidation:
    def test_objections_arrive_together_and_block_all(
        self,
    ):
        repo, addresses = build()
        tx = RefTransaction(repo=repo)
        tx.stage("main", addresses[0])
        tx.stage("ghost", delete=True)
        tx.stage("feature", "f" * 20)
        before = dict(repo.refs.branches)
        with pytest.raises(Invalid) as caught:
            tx.apply()
        message = str(caught.value)
        assert "3 objection(s), nothing applied" in (
            message
        )
        assert "would rewind" in message
        assert "does not exist to delete" in message
        assert "not a commit here" in message
        assert repo.refs.branches == before

    def test_a_double_named_pointer_is_two_decisions(
        self,
    ):
        repo, addresses = build()
        tx = RefTransaction(repo=repo)
        tx.stage("feature", addresses[0], force=True)
        tx.stage("feature", addresses[1])
        with pytest.raises(Invalid) as caught:
            tx.apply()
        assert "two decisions" in str(caught.value)

    def test_an_empty_transaction_decides_nothing(self):
        repo, _addresses = build()
        with pytest.raises(Invalid):
            RefTransaction(repo=repo).apply()


class TestApplication:
    def test_the_batch_applies_with_an_itinerary(self):
        repo, addresses = build()
        third = repo.commit(
            {"a.py": b"1\n2\n3\n"}, "three"
        )
        tx = RefTransaction(repo=repo)
        tx.stage("release", third.address)
        tx.stage(
            "feature", addresses[0], force=True
        )
        receipt = tx.apply()
        assert receipt.startswith(
            "applied 2 move(s) as one decision:"
        )
        assert "release: born at" in receipt
        assert "feature:" in receipt
        assert repo.refs.branches["release"] == (
            third.address
        )
        assert repo.refs.branches["feature"] == (
            addresses[0]
        )
        assert tx.moves == []

    def test_retirement_rides_the_same_decision(self):
        repo, _addresses = build()
        third = repo.commit(
            {"a.py": b"1\n2\n3\n"}, "three"
        )
        repo.refs.checkout("main")
        tx = RefTransaction(repo=repo)
        tx.stage("main", third.address)
        tx.stage("feature", delete=True)
        receipt = tx.apply()
        assert "feature: retired from" in receipt
        assert "feature" not in repo.refs.branches
