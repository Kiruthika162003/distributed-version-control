from __future__ import annotations

import pytest

from keel.errors import Corrupt, Invalid
from keel.objects import ObjectStore
from keel.repo import Repo
from keel.transfer import negotiate, receipt, receive

BASE = {"app.py": b"v1", "lib.py": b"shared"}


def history() -> tuple[Repo, str, str]:
    repo = Repo.init()
    early = repo.commit(dict(BASE), "base").address
    repo.commit(dict(BASE, **{"app.py": b"v2"}), "second")
    late = repo.commit(
        dict(BASE, **{"app.py": b"v3"}), "third"
    ).address
    return repo, early, late


class TestNegotiation:
    def test_only_the_difference_crosses_the_wire(self):
        repo, early, late = history()
        incremental = negotiate(
            repo, wants=[late], haves=[early]
        )
        full = negotiate(repo, wants=[late], haves=[])
        assert incremental.size() < full.size()

    def test_the_receipt_prices_the_negotiation(self):
        repo, early, late = history()
        batch = negotiate(repo, wants=[late], haves=[early])
        line = receipt(repo, [late], batch)
        assert "where a full clone ships" in line
        assert "the negotiation saved" in line

    def test_shared_blobs_never_ship_twice(self):
        repo, early, late = history()
        batch = negotiate(repo, wants=[late], haves=[early])
        shipped_payloads = [
            payload
            for _, payload in batch.objects.values()
        ]
        assert shipped_payloads.count(b"shared") == 0

    def test_wanting_nothing_is_a_ping(self):
        repo, _, _ = history()
        with pytest.raises(Invalid):
            negotiate(repo, wants=[], haves=[])


class TestReceiving:
    def test_a_batch_round_trips_into_an_empty_store(self):
        repo, _, late = history()
        batch = negotiate(repo, wants=[late], haves=[])
        target = ObjectStore()
        verdict = receive(target, batch)
        assert "0 already held" in verdict
        assert target.has(late)

    def test_one_wrong_object_poisons_the_whole_batch(self):
        repo, _, late = history()
        batch = negotiate(repo, wants=[late], haves=[])
        victim = next(iter(batch.objects))
        kind, _ = batch.objects[victim]
        batch.objects[victim] = (kind, b"tampered in flight")
        target = ObjectStore()
        with pytest.raises(Corrupt) as caught:
            receive(target, batch)
        assert "forfeited the benefit of the doubt" in str(
            caught.value
        )
        assert target.writes == 0

    def test_receiving_twice_admits_nothing_new(self):
        repo, _, late = history()
        batch = negotiate(repo, wants=[late], haves=[])
        target = ObjectStore()
        receive(target, batch)
        verdict = receive(target, batch)
        assert verdict.startswith("0 object(s) admitted")
