"""Bundles: a repository in an envelope, for the network that is not there.

Air-gapped machines, review by email, a backup that survives
the hosting provider: sometimes history must travel as a
file. A bundle packages a set of objects plus the branch tips
they support, with a manifest digest over the sorted contents
so tampering in transit has a name, and it can be full or
incremental: an incremental bundle declares its basis, the
commits the receiver must already hold, and verification
against a repository checks the basis before unbundling
because applying an incremental bundle to a repository
missing its basis produces amputated history with a valid
checksum, the most convincing kind of broken. Unbundling is
receive-verified like any transfer, and the listing renders
what the envelope holds without opening it into a store,
since inspecting mail before trusting it is the entire
etiquette of mail.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from keel.errors import Corrupt, Invalid, Missing
from keel.objects import COMMIT, digest_bytes
from keel.repo import Repo
from keel.transfer import negotiate


@dataclass
class Bundle:
    tips: dict[str, str]
    basis: tuple[str, ...]
    objects: dict[str, tuple[str, bytes]] = field(
        default_factory=dict
    )

    def manifest_digest(self) -> str:
        folded = hashlib.sha256()
        for address in sorted(self.objects):
            kind, payload = self.objects[address]
            folded.update(address.encode())
            folded.update(kind.encode())
            folded.update(payload)
        for name in sorted(self.tips):
            folded.update(name.encode())
            folded.update(self.tips[name].encode())
        return folded.hexdigest()[:20]

    def listing(self) -> str:
        commits = sum(
            1
            for kind, _ in self.objects.values()
            if kind == COMMIT
        )
        kind_word = (
            "incremental" if self.basis else "full"
        )
        lines = [
            f"{kind_word} bundle: {len(self.objects)} "
            f"object(s), {commits} commit(s), manifest "
            f"{self.manifest_digest()[:8]}"
        ]
        for name, address in sorted(self.tips.items()):
            lines.append(f"  tip {name} -> {address[:8]}")
        for address in self.basis:
            lines.append(
                f"  requires {address[:8]} at the receiver"
            )
        return "\n".join(lines)


def create_bundle(
    repo: Repo,
    branches: list[str],
    basis: list[str] | None = None,
) -> tuple[Bundle, str]:
    if not branches:
        raise Invalid("an empty envelope is stationery")
    tips = {}
    for name in branches:
        tip = repo.refs.branches.get(name)
        if tip is None:
            raise Missing(f"{name} is not a branch")
        tips[name] = tip
    batch = negotiate(
        repo,
        wants=list(tips.values()),
        haves=list(basis or []),
    )
    bundle = Bundle(
        tips=tips,
        basis=tuple(basis or []),
        objects=dict(batch.objects),
    )
    return bundle, bundle.manifest_digest()


def unbundle(
    target: Repo,
    bundle: Bundle,
    expected_manifest: str,
) -> str:
    if bundle.manifest_digest() != expected_manifest:
        raise Corrupt(
            "the manifest does not match; tampering in "
            "transit now has a name"
        )
    for required in bundle.basis:
        if required not in target.graph.commits:
            raise Invalid(
                f"the basis commit {required[:8]} is not "
                "here; applying this bundle anyway produces "
                "amputated history with a valid checksum, "
                "the most convincing kind of broken"
            )
    for address, (kind, payload) in bundle.objects.items():
        if digest_bytes(kind, payload) != address:
            raise Corrupt(
                f"{address[:8]} does not match its bytes"
            )
    admitted = 0
    for address, (kind, payload) in bundle.objects.items():
        if not target.store.has(address):
            target.store.put(kind, payload)
            admitted += 1
    return (
        f"unbundled {admitted} object(s); "
        f"{len(bundle.tips)} tip(s) available to adopt"
    )
