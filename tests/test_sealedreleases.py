from __future__ import annotations

import pytest

from keel.errors import Corrupt
from keel.repo import Repo
from keel.sealedreleases import (
    SealedRelease,
    seal,
    verify,
)
from keel.signing import Keyring, Signature
from keel.tags import TagStore


def build() -> tuple[Repo, TagStore, Keyring]:
    repo = Repo.init()
    tip = repo.commit(
        {"app.py": b"core\n", "README": b"r\n"},
        "the release state",
    )
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", tip.address, "first cut")
    keyring = Keyring()
    keyring.enroll("avery", "orchard-gate-11")
    return repo, tags, keyring


class TestTheChain:
    def test_seal_and_verify_walk_end_to_end(self):
        repo, tags, keyring = build()
        release = seal(
            repo, tags, keyring, "v1.0", "avery"
        )
        assert release.version == "v1.0"
        assert "app.py" in release.manifest
        verdict = verify(repo, keyring, release)
        assert verdict.startswith("v1.0 at ")
        assert "manifest matches" in verdict
        assert "valid: avery vouched" in verdict

    def test_a_stranger_keeper_is_named(self):
        repo, tags, keyring = build()
        release = seal(
            repo, tags, keyring, "v1.0", "avery"
        )
        other = Keyring()
        other.enroll("someone", "other-key-1234")
        verdict = verify(repo, other, release)
        assert "stranger:" in verdict

    def test_a_forged_mark_is_named(self):
        repo, tags, keyring = build()
        release = seal(
            repo, tags, keyring, "v1.0", "avery"
        )
        forged = SealedRelease(
            version=release.version,
            address=release.address,
            manifest=release.manifest,
            manifest_digest=release.manifest_digest,
            signature=Signature(
                signer="avery",
                address=release.signature.address,
                mark="0" * 20,
            ),
        )
        verdict = verify(repo, keyring, forged)
        assert "forged:" in verdict

    def test_the_changed_crate_is_the_loudest_failure(
        self,
    ):
        repo, tags, keyring = build()
        release = seal(
            repo, tags, keyring, "v1.0", "avery"
        )
        tampered = SealedRelease(
            version=release.version,
            address=release.address,
            manifest=release.manifest,
            manifest_digest="f" * 20,
            signature=release.signature,
        )
        with pytest.raises(Corrupt) as caught:
            verify(repo, keyring, tampered)
        assert (
            "the seal intact on a changed crate"
        ) in str(caught.value)
