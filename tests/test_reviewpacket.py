from __future__ import annotations

from keel.codeowners import OwnersFile
from keel.repo import Repo
from keel.reviewpacket import packet

BASE = {
    "src/app.py": b"core\n",
    "docs/guide.md": b"g\n",
}


def build(move_trunk: bool = False) -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature")
    repo.refs.checkout("feature")
    repo.commit(
        dict(BASE, **{"src/app.py": b"core\nserve\n"}),
        "Wire the server cleanly",
    )
    repo.commit(
        dict(
            BASE,
            **{
                "src/app.py": b"core\nserve\n",
                "docs/guide.md": b"g\nserver notes\n",
            },
        ),
        "Document the server",
    )
    repo.refs.checkout("main")
    if move_trunk:
        repo.commit(
            dict(BASE, **{"src/app.py": b"core\nm\n"}),
            "Trunk moves on",
        )
    return repo


OWNERS = OwnersFile.parse(
    "src/ team-core\ndocs/ team-docs\n"
)


class TestTheEnvelope:
    def test_the_commit_list_is_divergence_only(self):
        repo = build()
        page = packet(repo, "main", "feature", OWNERS)
        assert "under review (2 commit(s)):" in page
        assert "Wire the server cleanly" in page
        assert "Document the server" in page
        assert "base" not in page.split("under review")[1]

    def test_a_still_trunk_promises_a_clean_landing(
        self,
    ):
        repo = build()
        page = packet(repo, "main", "feature", OWNERS)
        assert (
            "main has not moved; this will land as "
            "written"
        ) in page

    def test_a_moving_trunk_warns_about_the_merge(self):
        repo = build(move_trunk=True)
        page = packet(repo, "main", "feature", OWNERS)
        assert (
            "meanwhile, main moved 1 commit(s)"
        ) in page

    def test_the_landing_map_and_routing_ride_along(
        self,
    ):
        repo = build()
        page = packet(repo, "main", "feature", OWNERS)
        assert "where the change landed" in page
        assert (
            "owners: route to team-core, team-docs"
        ) in page

    def test_missing_owners_is_said_not_skipped(self):
        repo = build()
        page = packet(repo, "main", "feature")
        assert "routing skipped and said so" in page

    def test_lint_rides_as_advisory_context(self):
        repo = build()
        page = packet(repo, "main", "feature", OWNERS)
        assert "graded, not blocked" in page
        assert "lint finding(s) across the branch" in (
            page
        )
