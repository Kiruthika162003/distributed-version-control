from __future__ import annotations

import pytest

from keel.bundle import create_bundle, unbundle
from keel.errors import Corrupt, Invalid, Missing
from keel.repo import Repo

BASE = {"a.txt": b"one"}


def sender() -> tuple[Repo, str, str]:
    repo = Repo.init()
    early = repo.commit(dict(BASE), "base").address
    late = repo.commit(
        dict(BASE, **{"a.txt": b"two"}), "growth"
    ).address
    return repo, early, late


class TestTheEnvelope:
    def test_the_listing_inspects_without_opening(self):
        repo, _, _ = sender()
        bundle, _ = create_bundle(repo, ["main"])
        listing = bundle.listing()
        assert listing.startswith("full bundle:")
        assert "tip main -> " in listing

    def test_the_incremental_bundle_names_its_basis(self):
        repo, early, _ = sender()
        bundle, _ = create_bundle(
            repo, ["main"], basis=[early]
        )
        assert "incremental bundle" in bundle.listing()
        assert f"requires {early[:8]}" in bundle.listing()

    def test_the_empty_envelope_is_stationery(self):
        repo, _, _ = sender()
        with pytest.raises(Invalid):
            create_bundle(repo, [])

    def test_the_ghost_branch_is_missing(self):
        repo, _, _ = sender()
        with pytest.raises(Missing):
            create_bundle(repo, ["ghost"])


class TestUnbundling:
    def test_a_full_bundle_seeds_an_empty_repository(self):
        repo, _, late = sender()
        bundle, manifest = create_bundle(repo, ["main"])
        target = Repo.init()
        verdict = unbundle(target, bundle, manifest)
        assert "tip(s) available to adopt" in verdict
        assert target.store.has(late)

    def test_tampering_in_transit_has_a_name(self):
        repo, _, _ = sender()
        bundle, manifest = create_bundle(repo, ["main"])
        victim = next(iter(bundle.objects))
        kind, _ = bundle.objects[victim]
        bundle.objects[victim] = (kind, b"altered")
        with pytest.raises(Corrupt) as caught:
            unbundle(Repo.init(), bundle, manifest)
        assert "tampering in transit now has a name" in str(
            caught.value
        )

    def test_the_missing_basis_is_refused_with_the_reason(self):
        repo, early, _ = sender()
        bundle, manifest = create_bundle(
            repo, ["main"], basis=[early]
        )
        with pytest.raises(Invalid) as caught:
            unbundle(Repo.init(), bundle, manifest)
        assert "the most convincing kind of broken" in str(
            caught.value
        )
