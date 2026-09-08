"""The sneakernet accounting: full bundle, thin bundle, and the guard rail.

Six commits ride to an air-gapped machine in two trips. The
first trip carries everything, and the count is the whole
history's closure. The machine later falls two commits
behind, so the second trip declares the tip it already holds
as the basis, and the thin bundle carries only what sits
above it. The guess before measuring: six commits of one
file should make the full bundle 13 objects (6 commits, 6
trees, 6 blobs, minus shared structure), and the thin bundle
6 (2 commits, 2 trees, 2 blobs). Measured: the full bundle
is 18 because each edit makes a new blob and nothing is
shared except nothing, and the thin bundle is 6 as guessed.
The refusal is the half that earns the witness: the thin
bundle pressed onto a stranger machine that lacks the basis
is turned away by name, because applying it anyway would
produce amputated history with a valid checksum, the most
convincing kind of broken.
"""

from __future__ import annotations

from keel.bundle import create_bundle, unbundle
from keel.errors import Invalid
from keel.repo import Repo
from keel.witnesses.finding import Testimony


def _history() -> tuple[Repo, list[str]]:
    repo = Repo.init()
    addresses = []
    for step in range(6):
        commit = repo.commit(
            {"log.txt": f"entry {step}\n".encode()},
            f"entry {step}",
        )
        addresses.append(commit.address)
    return repo, addresses


def run() -> Testimony:
    repo, addresses = _history()
    full, full_manifest = create_bundle(repo, ["main"])

    far = Repo.init()
    unbundle(far, full, full_manifest)
    for address, (_kind, _payload) in full.objects.items():
        if address in repo.graph.commits:
            far.graph.commits[address] = repo.graph.get(
                address
            )
    far.refs.create_branch("main", addresses[3])

    thin, thin_manifest = create_bundle(
        repo, ["main"], basis=[addresses[3]]
    )
    stranger = Repo.init()
    refused = False
    try:
        unbundle(stranger, thin, thin_manifest)
    except Invalid:
        refused = True

    numbers = {
        "full_objects": len(full.objects),
        "thin_objects": len(thin.objects),
        "savings": len(full.objects) - len(thin.objects),
        "stranger_refused": refused,
    }
    holds = (
        numbers["full_objects"] == 18
        and numbers["thin_objects"] == 6
        and numbers["savings"] == 12
        and numbers["stranger_refused"]
    )
    return Testimony(
        witness="bundleproof",
        claim=(
            "the full trip carries 18 objects, the thin "
            "trip above a declared basis carries 6, and "
            "the stranger machine without the basis is "
            "refused by name, because amputated history "
            "with a valid checksum is the most convincing "
            "kind of broken"
        ),
        numbers=numbers,
        holds=holds,
    )
