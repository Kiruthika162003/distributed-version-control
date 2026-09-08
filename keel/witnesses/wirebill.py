"""The wire bill: ten commits, one fetch, and the frontier does the saving.

A ten-commit history of one edited file and one untouched
library weighs 31 objects as a full clone: ten commits, ten
root trees, ten distinct app blobs, and one library blob that
content addressing stores once however often it appears. The
fetch that already holds commit five ships 15, the five new
commits with their trees and blobs, and the guess worth
recording is the one the arithmetic corrected: fifteen is not
half of thirty-one because the saved half also contains the
shared library blob and the first tree, objects the have-set
covers exactly once, so negotiation savings compound with
dedup instead of merely halving. The untouched library never
ships at all in the incremental batch, which is the sentence
that justifies the whole negotiation protocol.
"""

from __future__ import annotations

from keel.repo import Repo
from keel.transfer import negotiate
from keel.witnesses.finding import Testimony


def run() -> Testimony:
    repo = Repo.init()
    files = {
        "app.py": b"line\n" * 20,
        "lib.py": b"shared\n" * 30,
    }
    repo.commit(dict(files), "c0")
    addresses = [repo.refs.current()]
    for number in range(1, 10):
        files["app.py"] = (
            b"line\n" * 20 + f"edit {number}\n".encode()
        )
        addresses.append(
            repo.commit(dict(files), f"c{number}").address
        )
    full = negotiate(repo, wants=[addresses[-1]], haves=[])
    incremental = negotiate(
        repo, wants=[addresses[-1]], haves=[addresses[4]]
    )
    lib_blob = repo.trees.entry_at(
        repo.graph.get(addresses[-1]).tree, "lib.py"
    )
    numbers = {
        "full_clone_objects": full.size(),
        "incremental_objects": incremental.size(),
        "saved": full.size() - incremental.size(),
        "library_shipped_incrementally": lib_blob
        in incremental.objects,
    }
    holds = (
        numbers["full_clone_objects"] == 31
        and numbers["incremental_objects"] == 15
        and numbers["saved"] == 16
        and not numbers["library_shipped_incrementally"]
    )
    return Testimony(
        witness="wirebill",
        claim=(
            "the incremental fetch ships 15 of 31 objects and "
            "the untouched library never ships at all; "
            "negotiation savings compound with dedup instead "
            "of merely halving"
        ),
        numbers=numbers,
        holds=holds,
    )
