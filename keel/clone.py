"""Clone: the full copy made honestly, then made to prove it.

Every clone claims completeness; this one is audited on the
spot. The porcelain runs the standing machinery, negotiate
for everything the source's branches reach, receive into a
fresh store, the graph taught from the shipped commits, and
every branch adopted at the address the source holds, and
then, the part other clones skip, the graph diff runs
between source and copy and the clone refuses to hand over
a repository the diff calls anything but identical, because
a clone that might be partial is a backup that might be a
rumor, and the moment to find out is now, not during the
restore. The receipt carries the diff's own verdict line,
identical to the address, so the completeness claim arrives
as a measurement, in this workshop's oldest habit, rather
than as the word clone implying it.
"""

from __future__ import annotations

from keel.errors import Corrupt
from keel.graphdiff import compare, report
from keel.repo import Repo
from keel.transfer import negotiate, receive


def clone(source: Repo) -> tuple[Repo, str]:
    copy = Repo.init()
    wants = list(source.refs.branches.values())
    if wants:
        batch = negotiate(source, wants=wants, haves=[])
        receive(copy.store, batch)
        for address, (kind, _payload) in (
            batch.objects.items()
        ):
            if kind == "commit":
                copy.graph.commits[address] = (
                    source.graph.get(address)
                )
    for branch, tip in sorted(
        source.refs.branches.items()
    ):
        copy.refs.create_branch(branch, tip)
    if source.refs.head:
        copy.refs.checkout(source.refs.head)
    sides = compare(source, copy)
    if sides["only_here"] or sides["only_there"]:
        raise Corrupt(
            "the clone failed its own audit; a copy "
            "that might be partial is a backup that "
            "might be a rumor, and the moment to "
            "find out is now:\n"
            + report(source, copy)
        )
    verdict = report(source, copy).splitlines()[-1]
    return copy, (
        f"cloned {len(copy.graph.commits)} commit(s) "
        f"and {len(copy.refs.branches)} branch(es); "
        + verdict
    )
