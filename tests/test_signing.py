from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.signing import Keyring, Signature, SignedLedger


def build() -> tuple[Repo, list[str]]:
    repo = Repo.init()
    first = repo.commit({"app.py": b"1\n"}, "begin")
    second = repo.commit({"app.py": b"1\n2\n"}, "grow")
    third = repo.commit({"app.py": b"1\n2\n3\n"}, "more")
    return repo, [
        first.address,
        second.address,
        third.address,
    ]


def enrolled() -> Keyring:
    ring = Keyring()
    ring.enroll("kiruthika", "orchard-gate-11")
    return ring


class TestKeyring:
    def test_short_secrets_are_refused(self):
        with pytest.raises(Invalid) as caught:
            Keyring().enroll("someone", "abc")
        assert "password hint" in str(caught.value)

    def test_double_enrollment_is_refused(self):
        ring = enrolled()
        with pytest.raises(Invalid) as caught:
            ring.enroll("kiruthika", "different-key-22")
        assert "old marks stay checkable" in str(
            caught.value
        )

    def test_signing_without_enrollment_is_just_typing(
        self,
    ):
        with pytest.raises(Missing) as caught:
            Keyring().sign("ghost", "aa" * 10)
        assert "just typing" in str(caught.value)

    def test_a_valid_mark_names_its_voucher(self):
        ring = enrolled()
        signature = ring.sign("kiruthika", "aa" * 10)
        assert ring.verdict(signature) == (
            "valid: kiruthika vouched"
        )

    def test_a_forged_mark_is_named_forged(self):
        ring = enrolled()
        honest = ring.sign("kiruthika", "aa" * 10)
        forged = Signature(
            signer=honest.signer,
            address=honest.address,
            mark="0" * 20,
        )
        assert ring.verdict(forged).startswith("forged:")

    def test_a_stranger_is_named_a_stranger(self):
        ring = enrolled()
        other = Keyring()
        other.enroll("intruder", "sneaky-key-99")
        theirs = other.sign("intruder", "aa" * 10)
        assert ring.verdict(theirs).startswith("stranger:")


class TestChain:
    def test_a_fully_signed_chain_verifies_to_the_root(
        self,
    ):
        repo, addresses = build()
        ledger = SignedLedger(keyring=enrolled())
        for address in addresses:
            ledger.attach("kiruthika", address)
        page = ledger.chain(repo, addresses[-1])
        assert page == (
            "chain complete: 3 commit(s) verified back to "
            "the root, every link vouched"
        )

    def test_trust_ends_at_the_first_unsigned_link(self):
        repo, addresses = build()
        ledger = SignedLedger(keyring=enrolled())
        ledger.attach("kiruthika", addresses[2])
        ledger.attach("kiruthika", addresses[1])
        page = ledger.chain(repo, addresses[2])
        assert page.startswith(
            "trust extends 2 commit(s) from the tip"
        )
        assert addresses[0][:8] in page
        assert "unsigned wearing a lanyard" in page

    def test_a_forged_link_breaks_the_chain_where_it_lies(
        self,
    ):
        repo, addresses = build()
        ledger = SignedLedger(keyring=enrolled())
        for address in addresses:
            ledger.attach("kiruthika", address)
        honest = ledger.signatures[addresses[0]]
        ledger.signatures[addresses[0]] = Signature(
            signer=honest.signer,
            address=honest.address,
            mark="f" * 20,
        )
        page = ledger.chain(repo, addresses[-1])
        assert "trust extends 2 commit(s)" in page
        assert "forged" in page

    def test_a_merge_pauses_the_walk(self):
        repo, addresses = build()
        side = repo.graph.create(
            tree=repo.graph.get(addresses[0]).tree,
            parents=(addresses[0],),
            message="side",
        )
        merged = repo.commit_with_parents(
            {"app.py": b"merged\n"},
            "merge",
            (addresses[-1], side.address),
        )
        ledger = SignedLedger(keyring=enrolled())
        ledger.attach("kiruthika", merged.address)
        page = ledger.chain(repo, merged.address)
        assert "pauses at merge" in page
        assert "each parent line needs its own walk" in page
