"""Signing: a mark proves who vouched, a chain proves nobody skipped.

A signature here is a keyed digest over the commit address,
which is enough because the address already covers the tree,
the parents, and the message, so vouching for the address
vouches for all of it and everything upstream it names. The
keyring holds enrolled signers, and verification distinguishes
the three failures that get conflated in practice: an
unsigned commit, a commit signed by a stranger the keyring
never enrolled, and a forged mark that does not match the
key it claims, each a different conversation with a different
person. The chain walk is the part tools skip: verifying one
tip proves one commit, but a release is trustworthy only if
every commit back to the trusted root carries a valid mark,
so the walk reports how far trust extends and names the first
link that breaks it, because "mostly signed" is a phrase that
means unsigned wearing a lanyard.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo


def _mark(secret: str, address: str) -> str:
    return hashlib.sha256(
        f"{secret}|{address}".encode()
    ).hexdigest()[:20]


@dataclass(frozen=True)
class Signature:
    signer: str
    address: str
    mark: str


@dataclass
class Keyring:
    keys: dict[str, str] = field(default_factory=dict)

    def enroll(self, signer: str, secret: str) -> str:
        if not signer.strip():
            raise Invalid("a signer needs a name")
        if len(secret) < 8:
            raise Invalid(
                "a secret under eight characters is a "
                "password hint, not a key"
            )
        if signer in self.keys:
            raise Invalid(
                f"{signer} is already enrolled; rotating a "
                "key is a new enrollment under a new name, "
                "so the old marks stay checkable"
            )
        self.keys[signer] = secret
        return f"{signer} enrolled"

    def sign(self, signer: str, address: str) -> Signature:
        secret = self.keys.get(signer)
        if secret is None:
            raise Missing(
                f"{signer} holds no key here; signing "
                "without enrollment is just typing"
            )
        return Signature(
            signer=signer,
            address=address,
            mark=_mark(secret, address),
        )

    def verdict(self, signature: Signature) -> str:
        secret = self.keys.get(signature.signer)
        if secret is None:
            return (
                f"stranger: {signature.signer} is not in "
                "the keyring"
            )
        if _mark(secret, signature.address) != signature.mark:
            return (
                f"forged: the mark does not match "
                f"{signature.signer}'s key"
            )
        return f"valid: {signature.signer} vouched"


@dataclass
class SignedLedger:
    keyring: Keyring
    signatures: dict[str, Signature] = field(
        default_factory=dict
    )

    def attach(
        self, signer: str, address: str
    ) -> Signature:
        signature = self.keyring.sign(signer, address)
        self.signatures[address] = signature
        return signature

    def chain(self, repo: Repo, tip: str) -> str:
        walked = 0
        address = tip
        while True:
            commit = repo.graph.get(address)
            signature = self.signatures.get(address)
            if signature is None:
                return (
                    f"trust extends {walked} commit(s) from "
                    f"the tip and ends at {address[:8]} "
                    f"({commit.message[:30]!r}): unsigned; "
                    "mostly signed means unsigned wearing "
                    "a lanyard"
                )
            verdict = self.keyring.verdict(signature)
            if not verdict.startswith("valid"):
                return (
                    f"trust extends {walked} commit(s) from "
                    f"the tip and ends at {address[:8]}: "
                    f"{verdict}"
                )
            walked += 1
            if not commit.parents:
                return (
                    f"chain complete: {walked} commit(s) "
                    "verified back to the root, every link "
                    "vouched"
                )
            if len(commit.parents) > 1:
                return (
                    f"trust extends {walked} commit(s) and "
                    f"pauses at merge {address[:8]}; each "
                    "parent line needs its own walk"
                )
            address = commit.parents[0]
