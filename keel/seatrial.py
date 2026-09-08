"""The sea trial: one representative maneuver per system, run on demand.

Test suites certify the workshop for its builders; the sea
trial certifies it for a skeptic with five minutes, running
one honest maneuver through each major system in a scratch
repository and reporting each in a line. The store is asked
to hold and return bytes, the graph to refuse a time
traveler, the diff to merge clean edits and flag a true
collision, the shelf to hold and return work, the hunt to
find a planted culprit, the wire to ship only what the
receiver lacks, and the rewrite to fold a fixup silently.
Every maneuver asserts its own outcome and the trial stops
loudly on the first failure, a sea trial that continues
past a leak being a brochure cruise, and the closing line
counts systems exercised so the skeptic knows the tour
was the whole ship and not the good deck.
"""

from __future__ import annotations

from keel.autosquash import plan as autosquash_plan
from keel.bisectrun import AutoBisect
from keel.diff3 import is_clean, merge3
from keel.errors import Corrupt
from keel.objects import BLOB, ObjectStore
from keel.rebaseplan import execute
from keel.repo import Repo
from keel.stash import Stash
from keel.transfer import negotiate


def run_trial() -> str:
    passed: list[str] = []

    store = ObjectStore()
    address = store.put(BLOB, b"trial bytes\n")
    if store.get(address) != b"trial bytes\n":
        raise Corrupt("the store lost the trial bytes")
    passed.append(
        "store: held and returned the bytes"
    )

    repo = Repo.init()
    first = repo.commit(
        {"log.txt": b"one\n"}, "first"
    )
    repo.commit({"log.txt": b"one\ntwo\n"}, "second")
    if not repo.graph.is_ancestor(
        first.address, repo.refs.current()
    ):
        raise Corrupt(
            "the graph forgot its own ancestry"
        )
    passed.append("graph: ancestry holds")

    regions = merge3(
        "a\nb\nc\n", "A\nb\nc\n", "a\nb\nC\n"
    )
    collision = merge3("x\n", "ours\n", "theirs\n")
    if not is_clean(regions) or is_clean(collision):
        raise Corrupt(
            "diff3 misjudged a trial merge"
        )
    passed.append(
        "diff3: merged the clean, flagged the "
        "collision"
    )

    shelf = Stash()
    shelf.push({"wip.txt": b"half\n"}, "main", "trial")
    files, _receipt = shelf.pop("main")
    if files != {"wip.txt": b"half\n"}:
        raise Corrupt("the shelf returned other work")
    passed.append("shelf: held and returned the work")

    hunt_repo = Repo.init()
    good = hunt_repo.commit(
        {"flag.txt": b"fine\n"}, "good"
    )
    hunt_repo.commit(
        {"flag.txt": b"broken\n"}, "the culprit"
    )
    bad = hunt_repo.commit(
        {"flag.txt": b"broken\nmore\n"}, "later"
    )

    def oracle(candidate: str) -> int:
        held = hunt_repo.files_at(candidate)
        return (
            1
            if b"broken" in held.get("flag.txt", b"")
            else 0
        )

    culprit = AutoBisect(
        graph=hunt_repo.graph, oracle=oracle
    ).run(good.address, bad.address)
    if (
        hunt_repo.graph.get(culprit).message
        != "the culprit"
    ):
        raise Corrupt("the hunt blamed the innocent")
    passed.append("hunt: found the planted culprit")

    batch = negotiate(
        repo,
        wants=[repo.refs.current()],
        haves=[first.address],
    )
    if first.address in batch.objects:
        raise Corrupt(
            "the wire shipped what the receiver held"
        )
    passed.append(
        "wire: shipped only what was lacking"
    )

    fix_repo = Repo.init()
    base = fix_repo.commit(
        {"a.py": b"base\n"}, "ground"
    )
    fix_repo.commit({"a.py": b"work\n"}, "the work")
    tip = fix_repo.commit(
        {"a.py": b"work fixed\n"}, "fixup! the work"
    )
    result = execute(
        fix_repo,
        base.address,
        tip.address,
        autosquash_plan(
            fix_repo, base.address, tip.address
        ),
    )
    folded = fix_repo.graph.get(result.new_tip)
    if folded.message != "the work":
        raise Corrupt(
            "the rewrite kept the fixup noise"
        )
    passed.append(
        "rewrite: folded the fixup silently"
    )

    return "\n".join(
        [
            "sea trial:",
            *(f"  {line}" for line in passed),
            f"{len(passed)} system(s) exercised, all "
            "answered; the tour was the whole ship, "
            "not the good deck",
        ]
    )
