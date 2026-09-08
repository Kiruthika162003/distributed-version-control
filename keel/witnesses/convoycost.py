"""The scattered convoy billed: what a failed attempt leaves in the water.

The convoy promises the harbor looks untouched after a
failure, and the witness audits the promise at the level
where it is only mostly true: the branch table, exactly as
promised, does not move, but the private integration built
before the collision leaves its leg objects in the store,
flotsam of the attempt. The drill runs a convoy engineered
to scatter on its second leg and counts. The trunk pointer
is identical before and after, as promised. The store was
guessed heavier by two, the leg's commit and its tree, and
measured heavier by one: the merged tree already existed
as the branch's own tree, deduplication collapsing what
the guess counted twice, so the whole cost of the failed
attempt is a single commit object. The collection then
runs twice in the gcpin tradition, freeing nothing while
the keep-trunk-still reflog entries pin the flotsam and
freeing exactly the one object after fresh work pushes
the pins out. The promise survives with a footnote:
untouched means the names, and the bytes take one
collection cycle to agree.
"""

from __future__ import annotations

from keel.convoy import land_convoy
from keel.errors import Conflict
from keel.gc import Collector
from keel.repo import Repo
from keel.witnesses.finding import Testimony

BASE = {
    "api.py": b"api\n",
    "caller.py": b"c1\n",
}


def _arena() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("api-change")
    repo.refs.checkout("api-change")
    repo.commit(
        dict(BASE, **{"api.py": b"api v2\n"}),
        "api work",
    )
    repo.refs.checkout("main")
    repo.branch_from_head("rogue")
    repo.refs.checkout("rogue")
    repo.commit(
        dict(BASE, **{"api.py": b"api rogue\n"}),
        "rogue work",
    )
    repo.refs.checkout("main")
    return repo


def run() -> Testimony:
    repo = _arena()
    trunk_before = repo.refs.branches["main"]
    objects_before = len(repo.store.objects)
    scattered = False
    try:
        land_convoy(
            repo,
            "main",
            ["api-change", "rogue"],
            lambda _files: None,
        )
    except Conflict:
        scattered = True
    flotsam = len(repo.store.objects) - objects_before

    collector = Collector(repo=repo)
    held = len(repo.store.objects)
    collector.collect()
    freed_pinned = held - len(repo.store.objects)

    repo.commit(
        dict(BASE, **{"caller.py": b"c1 fresh\n"}),
        "fresh work",
    )
    collector.trim_reflog(keep_last=1)
    held = len(repo.store.objects)
    collector.collect()
    freed_after = held - len(repo.store.objects)

    numbers = {
        "scattered": scattered,
        "trunk_untouched": (
            trunk_before == repo.graph.log(
                repo.refs.branches["main"]
            )[1].address
        ),
        "flotsam_objects": flotsam,
        "freed_while_pinned": freed_pinned,
        "freed_after_trim": freed_after,
    }
    holds = (
        numbers["scattered"]
        and numbers["trunk_untouched"]
        and numbers["flotsam_objects"] == 1
        and numbers["freed_while_pinned"] == 0
        and numbers["freed_after_trim"] == 1
    )
    return Testimony(
        witness="convoycost",
        claim=(
            "the scattered convoy leaves the trunk "
            "name exactly where it stood and one "
            "flotsam object, the merge commit alone, "
            "the guessed second object having been "
            "deduplicated away; pinned through one "
            "collection and freed by the next, "
            "untouched means the names, and the "
            "bytes take one cycle to agree"
        ),
        numbers=numbers,
        holds=holds,
    )
