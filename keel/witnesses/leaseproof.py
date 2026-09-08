"""The push race run twice: once with a hammer, once with a lease.

The same race both times. A shared repository holds two
commits, our developer fetches and starts rewriting, and a
colleague pushes one commit into the gap. In the hammer run
the developer bare-forces their replacement tip and the drill
counts the bodies: the colleague's commit is no longer
reachable from any branch, orphaned by a push that never knew
it existed. In the lease run the developer pushes with the
tip they believed the remote held, the lease detects that the
belief went stale, and the push bounces with both tips named
while the colleague's commit stays reachable. The measured
difference between the runs is exactly one orphaned commit,
which is the whole argument for the lease stated as
arithmetic: force-with-lease costs one extra argument and
saves precisely the commit somebody else was standing on.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.push import PushGate
from keel.remotes import RemoteSet
from keel.repo import Repo
from keel.witnesses.finding import Testimony


def _race(
    use_lease: bool,
) -> tuple[int, bool]:
    shared = Repo.init()
    developer = Repo.init()
    developer.commit({"app.py": b"one\n"}, "begin")
    developer.commit({"app.py": b"one\ntwo\n"}, "grow")
    gate = PushGate(remote=shared)
    gate.push(developer, "main")
    believed = shared.refs.branches["main"]

    colleague = Repo.init()
    lookout = RemoteSet(local=colleague)
    lookout.add("origin", shared)
    lookout.fetch("origin")
    colleague.refs.create_branch("main", believed)
    colleague.refs.checkout("main")
    colleague.commit(
        {"app.py": b"one\ntwo\ncolleague\n"}, "in the gap"
    )
    gate.push(colleague, "main")
    gap_commit = colleague.refs.branches["main"]

    developer.commit(
        {"app.py": b"one\nrewritten\n"}, "rewrite"
    )
    bounced = False
    if use_lease:
        try:
            gate.push_with_lease(
                developer, "main", believed
            )
        except Invalid:
            bounced = True
    else:
        gate.push(developer, "main", force=True)

    reachable = shared.graph.ancestors(
        shared.refs.branches["main"]
    )
    orphaned = 0 if gap_commit in reachable else 1
    return orphaned, bounced


def run() -> Testimony:
    hammer_orphans, hammer_bounced = _race(use_lease=False)
    lease_orphans, lease_bounced = _race(use_lease=True)
    numbers = {
        "hammer_orphans": hammer_orphans,
        "hammer_bounced": hammer_bounced,
        "lease_orphans": lease_orphans,
        "lease_bounced": lease_bounced,
    }
    holds = (
        hammer_orphans == 1
        and not hammer_bounced
        and lease_orphans == 0
        and lease_bounced
    )
    return Testimony(
        witness="leaseproof",
        claim=(
            "the same race run twice: the bare force orphans "
            "exactly one commit, the lease bounces and "
            "orphans none, so force-with-lease costs one "
            "extra argument and saves precisely the commit "
            "somebody else was standing on"
        ),
        numbers=numbers,
        holds=holds,
    )
