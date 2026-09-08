"""A messy day: shelved work, one hand-resolved conflict, and its free twin.

An interruption forces the half-done rewrite onto the shelf,
the hotfix collides with the feature when they meet, a human
settles it once, and the recorder replays that answer when
the release branch hits the identical collision. The shelf
gets the last word: applying old work on the wrong branch
warns instead of pretending. Run with:
python -m examples.messyday
"""

from __future__ import annotations

from keel.merge import commit_merge, merge_commits
from keel.repo import Repo
from keel.rerere import Recorder
from keel.resolve import ResolutionSession
from keel.stash import Stash

BASE = {"app.py": b"core\n", "config.ini": b"mode=calm\n"}


def main() -> int:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature")
    repo.refs.checkout("feature")

    shelf = Stash()
    print(
        "shelve:  "
        + shelf.push(
            {"app.py": b"core\nhalf\n"},
            "feature",
            "half-done app rewrite",
        )
    )
    repo.refs.checkout("main")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nfixed\n"}),
        "hotfix the crash",
    )
    repo.refs.checkout("feature")
    _, receipt = shelf.pop("feature")
    print(f"pop:     {receipt}")
    resumed = repo.commit(
        dict(BASE, **{"app.py": b"core\nfeature\n"}),
        "feature work resumed",
    )

    ours = repo.refs.branches["feature"]
    theirs = repo.refs.branches["main"]
    outcome = merge_commits(repo, ours, theirs)
    print(f"merge:   {outcome.report().splitlines()[0]}")
    session = ResolutionSession(
        outcome=outcome,
        left_files=repo.files_at(ours),
        right_files=repo.files_at(theirs),
    )
    resolution = b"core\nfixed\nfeature\n"
    session.settle_by_hand("app.py", resolution)
    session.conclude()
    recorder = Recorder()
    base_text = repo.files_at(outcome.base)["app.py"]
    print(
        "record:  "
        + recorder.record(
            base_text,
            b"core\nfeature\n",
            b"core\nfixed\n",
            resolution,
        )
    )
    merged = commit_merge(repo, outcome, "merge the hotfix")
    print(
        f"landed:  {merged.address[:8]} with "
        f"{len(merged.parents)} parents"
    )

    repo.refs.create_branch("release", resumed.address)
    repo.refs.checkout("release")
    twin = merge_commits(repo, resumed.address, theirs)
    print(f"again:   {twin.report().splitlines()[0]}")
    replayed = recorder.replay(
        base_text, b"core\nfeature\n", b"core\nfixed\n"
    )
    text, note = replayed
    print(f"replay:  {note}")
    twin_session = ResolutionSession(
        outcome=twin,
        left_files=repo.files_at(resumed.address),
        right_files=repo.files_at(theirs),
    )
    twin_session.settle_by_hand("app.py", text)
    twin_session.conclude()
    commit_merge(repo, twin, "release takes the hotfix")
    print(f"ledger:  {recorder.ledger()}")

    print(
        "shelve:  "
        + shelf.push(
            {"notes.txt": b"midnight idea\n"},
            "feature",
            "midnight idea",
        )
    )
    repo.refs.checkout("main")
    _, warned = shelf.apply("main")
    print(f"apply:   {warned}")
    print(f"drop:    {shelf.drop(0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
