"""A commissioning day: founded, rehearsed, quoted, cloned, and spliced.

A new repository is scaffolded with its plan of a first
commit, the newcomer rehearses their landing with the pilot
aboard, the bill of lading quotes the freight before the
first push, the clone proves itself identical, and the old
archive is spliced beneath the new work so blame reaches
the founding. Run with: python -m examples.commissioningday
"""

from __future__ import annotations

from keel.blame import blame
from keel.branchpolicy import NamingPolicy
from keel.clone import clone
from keel.lading import bill
from keel.pilotage import rehearse
from keel.repo import Repo
from keel.scaffold import found
from keel.splice import splice


def main() -> int:
    repo = Repo.init()
    _commit, receipt = found(
        repo,
        "lanternfish",
        "A catalog of deep-sea observations.",
    )
    print(receipt.split(";")[0])

    page = rehearse(
        "feature/first-observation",
        (
            "Add the first observation\n\n"
            "One anglerfish, photographed twice.\n"
        ),
        ["observations/anglerfish.md"],
        policy=NamingPolicy(),
    )
    print(page.splitlines()[-1])

    files = dict(repo.head_files())
    files["observations/anglerfish.md"] = (
        b"one anglerfish, photographed twice\n"
    )
    repo.commit(files, "Add the first observation")
    remote = Repo.init()
    quote = bill(repo, remote, "main")
    print(quote.splitlines()[0])

    copy, clone_receipt = clone(repo)
    print(clone_receipt)

    archive = Repo.init()
    archive.commit(
        {"observations/log.md": b"old log begins\n"},
        "the expedition log opens",
    )
    resumed = Repo.init()
    resumed.commit(
        {"observations/log.md": b"old log begins\n"},
        "resumed from the archive",
    )
    resumed.commit(
        {
            "observations/log.md": (
                b"old log begins\nnew voyage\n"
            )
        },
        "the new voyage",
    )
    joined, splice_receipt = splice(archive, resumed)
    print(splice_receipt.split(", seam")[0])
    rows = blame(
        joined,
        joined.refs.current(),
        "observations/log.md",
    )
    first_author = joined.graph.get(
        rows[0].commit
    ).message
    print(
        f"blame reaches: {first_author!r} across "
        "the seam"
    )
    print(f"copy branches: {len(copy.refs.branches)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
