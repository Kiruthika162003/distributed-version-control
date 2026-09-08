"""A first voyage: init, commit, branch, merge, and the log that resulted.

Run with: python -m examples.firstvoyage
"""

from __future__ import annotations

from keel.merge import commit_merge, merge_commits
from keel.repo import Repo


def main() -> int:
    repo = Repo.init()
    repo.commit(
        {"README": b"a small project", "app.py": b"start"},
        "first light",
    )
    repo.commit(
        {"README": b"a small project", "app.py": b"start\nmore"},
        "grow the app",
    )
    print(f"log:     {len(repo.history())} commit(s) on main")

    repo.branch_from_head("feature")
    repo.refs.checkout("feature")
    repo.commit(
        {
            "README": b"a small project",
            "app.py": b"start\nmore",
            "feature.py": b"new idea",
        },
        "sketch the feature",
    )
    repo.refs.checkout("main")
    repo.commit(
        {
            "README": b"a small project, documented",
            "app.py": b"start\nmore",
        },
        "polish the readme",
    )

    outcome = merge_commits(
        repo,
        repo.refs.branches["main"],
        repo.refs.branches["feature"],
    )
    print(f"merge:   {outcome.report()}")
    merged = commit_merge(repo, outcome, "land the feature")
    print(
        f"landed:  {merged.address[:8]} with "
        f"{len(merged.parents)} parents"
    )
    files = repo.head_files()
    print(
        f"tree:    {len(files)} file(s), readme says "
        f"{files['README'].decode()!r}"
    )
    print(f"store:   {repo.store.ledger()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
