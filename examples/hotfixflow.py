"""The hotfix flow: fix on main, pick to release, tag, and revert the bad idea.

Run with: python -m examples.hotfixflow
"""

from __future__ import annotations

from keel.cherrypick import cherry_pick, revert
from keel.patchid import narrate_cherry
from keel.repo import Repo
from keel.tags import TagStore

BASE = {"app.py": b"stable", "config.ini": b"debug=false"}


def main() -> int:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", repo.refs.current(), "the shipped release")
    repo.branch_from_head("release-1.x")

    fix = repo.commit(
        dict(BASE, **{"app.py": b"patched"}),
        "fix: close the auth bypass",
    )
    bad = repo.commit(
        dict(
            BASE,
            **{"app.py": b"patched", "config.ini": b"debug=true"},
        ),
        "enable debug in prod",
    )
    undone = revert(repo, bad.address)
    print(f"revert:  {undone.message}")

    repo.refs.checkout("release-1.x")
    picked = cherry_pick(repo, fix.address)
    print(f"picked:  {picked.message}")
    tags.place(
        "v1.0.1",
        repo.refs.current(),
        "the auth bypass hotfix",
    )
    print(f"tagged:  {tags.describe(repo.refs.current())}")

    story = narrate_cherry(
        repo,
        repo.refs.branches["main"],
        repo.refs.branches["release-1.x"],
    )
    print(f"cherry:  {story.splitlines()[0]}")
    print(f"journal: {repo.refs.recent_log(1)[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
