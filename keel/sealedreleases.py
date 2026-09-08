"""Sealed releases: the manifest signed, the chain checkable end to end.

An archive proves its own integrity and a signature proves
who vouched, and the sealed release binds the two so a
recipient can walk the whole chain: the tag names the
commit, the archive's manifest lists what the commit
exports, and the mark over the manifest digest says a
named keeper saw exactly this list. Sealing signs the
digest rather than the archive bytes, since the manifest
already binds every entry and signing a summary of a
binding is how signatures stay small without staying
vague. Verification answers in the keyring's three
established voices, valid, stranger, or forged, plus the
one failure that is this module's own: a manifest that no
longer matches its archive, the seal intact on a changed
crate, which is reported as the loudest failure of the
four because it means tampering after the ceremony, and
ceremonies are exactly what tampering waits for.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.archive import export
from keel.errors import Corrupt
from keel.repo import Repo
from keel.signing import Keyring, Signature
from keel.tags import TagStore


@dataclass(frozen=True)
class SealedRelease:
    version: str
    address: str
    manifest: str
    manifest_digest: str
    signature: Signature


def seal(
    repo: Repo,
    tags: TagStore,
    keyring: Keyring,
    version: str,
    keeper: str,
) -> SealedRelease:
    address = tags.resolve(version)
    archive = export(repo, address)
    manifest = archive.manifest()
    digest = archive.archive_digest()
    signature = keyring.sign(keeper, digest)
    return SealedRelease(
        version=version,
        address=address,
        manifest=manifest,
        manifest_digest=digest,
        signature=signature,
    )


def verify(
    repo: Repo,
    keyring: Keyring,
    release: SealedRelease,
) -> str:
    archive = export(repo, release.address)
    if archive.archive_digest() != (
        release.manifest_digest
    ):
        raise Corrupt(
            f"{release.version}: the manifest no "
            "longer matches its archive, the seal "
            "intact on a changed crate; tampering "
            "after the ceremony, which is exactly "
            "what ceremonies are for"
        )
    verdict = keyring.verdict(release.signature)
    return (
        f"{release.version} at "
        f"{release.address[:8]}: manifest matches, "
        f"signature {verdict}"
    )
