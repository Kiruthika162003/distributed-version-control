from __future__ import annotations

from keel.codeowners import OwnersFile
from keel.freeze import FreezeBoard
from keel.gatekeeper import Gatekeeper, PushRequest
from keel.protect import BranchGuard, Protection

REVIEWED = (
    "Land the feature\n"
    "\n"
    "Reviewed-by: priya\n"
    "Reviewed-by: devi\n"
)


def build() -> Gatekeeper:
    guard = BranchGuard()
    guard.protect(
        Protection(pattern="main", required_reviews=2)
    )
    owners = OwnersFile.parse(
        "src/ team-core\ndocs/ team-docs\n"
    )
    return Gatekeeper(
        guard=guard, board=FreezeBoard(), owners=owners
    )


def request(**overrides) -> PushRequest:
    settings = {
        "branch": "main",
        "submitter": "dana",
        "messages": (REVIEWED,),
        "touched_paths": ("src/app.py", "docs/guide.md"),
        "force": False,
    }
    settings.update(overrides)
    return PushRequest(**settings)


class TestAcceptance:
    def test_a_clean_push_passes_every_gate(self):
        keeper = build()
        page = keeper.receive(request())
        assert page.startswith(
            "push of main by dana: ACCEPTED"
        )
        assert "freeze: [ok]" in page
        assert "reviews: [ok]" in page
        assert (
            "route to team-core, team-docs"
        ) in page
        assert "graded, not blocked" in page
        assert "the trip back is one" in page

    def test_the_journal_keeps_the_headline(self):
        keeper = build()
        keeper.receive(request())
        assert keeper.journal == [
            "push of main by dana: ACCEPTED"
        ]


class TestRefusals:
    def test_every_gate_speaks_even_after_a_failure(self):
        keeper = build()
        keeper.board.freeze(
            "main", "the release cut", "priya"
        )
        page = keeper.receive(
            request(messages=("no reviews here",))
        )
        assert "REFUSED, 2 hard failure(s)" in page
        assert "closed for the release cut" in page
        assert "0 review trailer(s) against 2" in page
        assert "owners: [ok]" in page
        assert "message: [ok]" in page

    def test_unowned_paths_breed_a_refusal(self):
        keeper = build()
        page = keeper.receive(
            request(
                touched_paths=(
                    "src/app.py",
                    "scripts/deploy.sh",
                )
            )
        )
        assert "REFUSED, 1 hard failure(s)" in page
        assert (
            "unowned path(s): scripts/deploy.sh"
        ) in page
        assert "how orphans breed" in page

    def test_force_is_refused_on_protected_branches(self):
        keeper = build()
        page = keeper.receive(request(force=True))
        assert "REFUSED, 1 hard failure(s)" in page
        assert "forced movement refused by rule main" in (
            page
        )

    def test_lint_findings_never_refuse_alone(self):
        keeper = build()
        sloppy = (
            "fixed stuff\n\nReviewed-by: priya\n"
            "Reviewed-by: devi\n"
        )
        page = keeper.receive(request(messages=(sloppy,)))
        assert "ACCEPTED" in page
        assert "graded, not blocked" in page


class TestOptionalGates:
    def test_a_missing_owners_file_is_named_not_faked(
        self,
    ):
        keeper = build()
        keeper.owners = None
        page = keeper.receive(request())
        assert "no owners file configured" in page
        assert "ACCEPTED" in page
