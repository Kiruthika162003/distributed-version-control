from __future__ import annotations

import pytest

from keel.errors import Corrupt
from keel.objects import BLOB
from keel.quarantine import Airlock
from keel.repo import Repo
from keel.transfer import negotiate


def shipment() -> tuple[Repo, object]:
    source = Repo.init()
    source.commit(
        {"app.py": b"core\n", "lib.py": b"lib\n"}, "begin"
    )
    source.commit(
        {"app.py": b"core\nmore\n", "lib.py": b"lib\n"},
        "grow",
    )
    batch = negotiate(
        source,
        wants=[source.refs.current()],
        haves=[],
    )
    return source, batch


class TestClearance:
    def test_a_clean_batch_clears_and_teaches_the_graph(
        self,
    ):
        source, batch = shipment()
        target = Repo.init()
        airlock = Airlock(target=target)
        receipt = airlock.admit(batch)
        assert "admitted" in receipt
        assert airlock.admitted == len(batch.objects)
        tip = source.refs.current()
        assert tip in target.graph.commits
        assert target.files_at(tip)["app.py"] == (
            b"core\nmore\n"
        )

    def test_inspection_predicts_without_admitting(self):
        _source, batch = shipment()
        target = Repo.init()
        airlock = Airlock(target=target)
        verdict = airlock.inspect(batch)
        assert "would clear the airlock" in verdict
        assert len(target.store.objects) == 0


class TestRejections:
    def test_one_lie_rejects_the_whole_shipment(self):
        _source, batch = shipment()
        victim = next(
            address
            for address, (kind, _payload) in (
                batch.objects.items()
            )
            if kind == BLOB
        )
        batch.objects[victim] = (BLOB, b"tampered\n")
        target = Repo.init()
        airlock = Airlock(target=target)
        with pytest.raises(Corrupt) as caught:
            airlock.admit(batch)
        message = str(caught.value)
        assert "wholesale, innocents included" in message
        assert "do not match the claimed address" in (
            message
        )
        assert len(target.store.objects) == 0
        assert airlock.rejected_batches == 1

    def test_a_tree_pointing_nowhere_is_named(self):
        _source, batch = shipment()
        doomed = next(
            address
            for address, (kind, _payload) in (
                batch.objects.items()
            )
            if kind == BLOB
        )
        del batch.objects[doomed]
        target = Repo.init()
        airlock = Airlock(target=target)
        with pytest.raises(Corrupt) as caught:
            airlock.admit(batch)
        assert "exists nowhere" in str(caught.value)

    def test_an_orphan_commit_is_named(self):
        source, _batch = shipment()
        tip_only = negotiate(
            source,
            wants=[source.refs.current()],
            haves=[
                source.graph.get(
                    source.refs.current()
                ).parents[0]
            ],
        )
        target = Repo.init()
        airlock = Airlock(target=target)
        with pytest.raises(Corrupt) as caught:
            airlock.admit(tip_only)
        assert "parent" in str(caught.value)
        assert "exists nowhere" in str(caught.value)

    def test_the_journal_counts_both_outcomes(self):
        source, batch = shipment()
        target = Repo.init()
        airlock = Airlock(target=target)
        airlock.admit(batch)
        fresh = negotiate(
            source,
            wants=[source.refs.current()],
            haves=[],
        )
        victim = next(iter(fresh.objects))
        kind, _payload = fresh.objects[victim]
        fresh.objects[victim] = (kind, b"garbage")
        with pytest.raises(Corrupt):
            airlock.admit(fresh)
        assert len(airlock.journal) == 2
        assert airlock.journal[0].startswith("admitted")
        assert airlock.journal[1].startswith("rejected")
