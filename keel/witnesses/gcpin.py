"""The reset-away commit, collected three times: pinned, still pinned, freed.

The career-saving property of the collector is structural,
not merciful, and this drill measures it twice over. Three
commits land, the branch is force-moved back one, and the
newest commit becomes unreachable from every ref while
remaining exactly the commit its author wants back before
lunch. The first collection frees nothing: the reflog entry
from the reset names the abandoned address and the census
honors the pin, no timer, no luck, just a journal line. The
first guess failed in a way worth keeping: trimming the
journal to its last line was supposed to unpin the commit,
and it freed nothing, because the last line WAS the reset
entry and a reset entry pins the very commit it abandoned.
The journal protects the abandoned address until newer work
pushes the entry out, which is better behavior than the
guess wanted. Only after a fresh commit moves the branch and
the trim drops the reset line does the third collection free
the private closure, measured at three: one commit, one
tree, one blob.
"""

from __future__ import annotations

from keel.gc import Collector
from keel.repo import Repo
from keel.witnesses.finding import Testimony


def run() -> Testimony:
    repo = Repo.init()
    repo.commit({"log.txt": b"one\n"}, "first")
    keeper = repo.commit({"log.txt": b"one\ntwo\n"}, "second")
    repo.commit({"log.txt": b"one\ntwo\nthree\n"}, "third")
    repo.refs.move(
        "main",
        keeper.address,
        reason="reset away the third",
        force=True,
    )
    collector = Collector(repo=repo)
    held_before = len(repo.store.objects)
    collector.collect()
    freed_pinned = held_before - len(repo.store.objects)

    collector.trim_reflog(keep_last=1)
    held_after_trim = len(repo.store.objects)
    collector.collect()
    freed_by_reset_line = held_after_trim - len(
        repo.store.objects
    )

    repo.commit(
        {"log.txt": b"one\ntwo\nfour\n"}, "a different third"
    )
    collector.trim_reflog(keep_last=1)
    held_after_movement = len(repo.store.objects)
    collector.collect()
    freed_at_last = held_after_movement - len(
        repo.store.objects
    )

    numbers = {
        "freed_while_pinned": freed_pinned,
        "freed_after_bare_trim": freed_by_reset_line,
        "freed_after_movement": freed_at_last,
        "survivors": len(repo.store.objects),
    }
    holds = (
        numbers["freed_while_pinned"] == 0
        and numbers["freed_after_bare_trim"] == 0
        and numbers["freed_after_movement"] == 3
        and numbers["survivors"] == held_after_movement - 3
    )
    return Testimony(
        witness="gcpin",
        claim=(
            "the reset-away commit survives the first "
            "collection on a reflog pin, survives the bare "
            "trim because the reset entry pins what it "
            "abandoned, and is freed as a private closure "
            "of exactly three only after newer work pushes "
            "the entry out"
        ),
        numbers=numbers,
        holds=holds,
    )
