"""The dedup bill: six branches, one library, and the store that noticed.

Six feature branches each snapshot a project whose shared
library never changes, and the drill counts what content
addressing quietly saves: the docstring first guessed
fifty-four references over eleven objects and the meter says
sixty-three over fifteen, with eighty-four put calls
collapsing to thirty actual writes and fifty-four answered
by an address that already existed. The corrected numbers
stay beside the guess, and the tree arithmetic is the
quieter half of the
finding: the shared lib subtree hashes identically in every
branch, so six root trees reference one lib tree, and the
did-anything-change question for the library is answered by
one comparison per branch forever. Deduplication here is not
a feature that was built; it is a consequence that was
noticed, which is the entire aesthetic of content addressing.
"""

from __future__ import annotations

from keel.repo import Repo
from keel.witnesses.finding import Testimony

LIB_FILES = {
    f"lib/mod{n}.py": f"library module {n}".encode()
    for n in range(8)
}


def run() -> Testimony:
    repo = Repo.init()
    base = dict(
        LIB_FILES, **{"app.py": b"main line"}
    )
    repo.commit(base, "base")
    lib_tree_addresses = set()
    for branch_number in range(6):
        name = f"topic-{branch_number}"
        repo.branch_from_head(name)
        repo.refs.checkout(name)
        files = dict(
            base,
            **{
                "app.py": (
                    f"branch {branch_number} work".encode()
                )
            },
        )
        commit = repo.commit(files, f"work on {name}")
        lib_tree_addresses.add(
            repo.trees.entry_at(
                repo.graph.get(commit.address).tree, "lib"
            )
        )
        repo.refs.checkout("main")
    blob_count = sum(
        1
        for kind, _ in repo.store.objects.values()
        if kind == "blob"
    )
    numbers = {
        "branches": 6,
        "logical_blob_refs": 7 * 9,
        "stored_blobs": blob_count,
        "put_calls": repo.store.writes
        + repo.store.dedup_hits,
        "actual_writes": repo.store.writes,
        "dedup_hits": repo.store.dedup_hits,
        "distinct_lib_trees": len(lib_tree_addresses),
    }
    holds = (
        numbers["stored_blobs"] == 15
        and numbers["distinct_lib_trees"] == 1
        and numbers["dedup_hits"] > 40
    )
    return Testimony(
        witness="dedupbill",
        claim=(
            "six branches reference one stored library: the "
            "shared lib subtree hashes identically "
            "everywhere, so did-anything-change is one "
            "comparison per branch forever, and dedup is not "
            "a feature that was built but a consequence that "
            "was noticed"
        ),
        numbers=numbers,
        holds=holds,
    )
