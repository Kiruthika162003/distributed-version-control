"""A feature week: branch, rebase onto moving main, resolve, and land.

Run with: python -m examples.featureweek
"""

from __future__ import annotations

from keel.history import review_summary
from keel.merge import commit_merge, merge_commits
from keel.rebase import rebase_branch
from keel.repo import Repo
from keel.resolve import ResolutionSession

BASE = {"app.py": b"core\nlogic", "docs.md": b"start"}


def main() -> int:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature")

    repo.commit(
        dict(BASE, **{"docs.md": b"start\npolished"}),
        "main polishes docs",
    )
    repo.refs.checkout("feature")
    repo.commit(
        dict(BASE, **{"feature.py": b"draft"}), "sketch"
    )
    repo.commit(
        dict(BASE, **{"feature.py": b"draft\nrefined"}),
        "refine",
    )

    story = rebase_branch(repo, "feature", "main")
    print(f"rebase:  {story[-1]}")

    repo.refs.checkout("main")
    repo.commit(
        dict(
            BASE,
            **{
                "docs.md": b"start\npolished",
                "app.py": b"MAIN\nlogic",
            },
        ),
        "main edits app",
    )
    repo.refs.checkout("feature")
    repo.commit(
        dict(
            BASE,
            **{
                "docs.md": b"start\npolished",
                "feature.py": b"draft\nrefined",
                "app.py": b"FEATURE\nlogic",
            },
        ),
        "feature edits app too",
    )
    repo.refs.checkout("main")

    left = repo.refs.branches["main"]
    right = repo.refs.branches["feature"]
    outcome = merge_commits(repo, left, right)
    print(f"merge:   {outcome.report().splitlines()[0]}")

    session = ResolutionSession(
        outcome=outcome,
        left_files=repo.files_at(left),
        right_files=repo.files_at(right),
    )
    session.settle_by_hand("app.py", b"MERGED\nlogic")
    session.conclude()
    print(f"settle:  {session.story().splitlines()[-1].strip()}")

    merged = commit_merge(repo, outcome, "land the feature")
    print(
        f"landed:  {merged.address[:8]} with "
        f"{len(merged.parents)} parents"
    )
    print(
        "review:  "
        + review_summary(repo, left, right).splitlines()[0]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
