"""The gatekeeper: every landing policy speaks once, in one trip.

Policies scattered across tools refuse one at a time, and
the submitter plays whack-a-mole: fix the reviews, discover
the freeze, fix the freeze, discover the unowned path. The
gatekeeper runs the whole gauntlet on every push and lets
every gate speak before the verdict, so a refusal arrives
as a complete list and the fix is one trip. The gates keep
their own voices, the freeze names who to ask, the review
count names the rule it fell short of, the owners file
names the orphan paths, because a gatekeeper that
paraphrases its gates turns five precise refusals into one
vague one. The message gate is advisory by contract and
cannot refuse anything alone, honoring the lint's own oath
that the goal is better messages, not fewer commits, and
the final page says plainly which failures were hard and
which lines are just the lint talking.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.codeowners import OwnersFile
from keel.commitlint import lint_message
from keel.errors import Conflict, Invalid
from keel.freeze import FreezeBoard
from keel.protect import BranchGuard


@dataclass(frozen=True)
class PushRequest:
    branch: str
    submitter: str
    messages: tuple[str, ...]
    touched_paths: tuple[str, ...]
    force: bool = False


@dataclass
class GateVerdict:
    gate: str
    verdict: str
    hard_failure: bool

    def line(self) -> str:
        mark = "REFUSE" if self.hard_failure else "ok"
        return f"  {self.gate}: [{mark}] {self.verdict}"


@dataclass
class Gatekeeper:
    guard: BranchGuard
    board: FreezeBoard
    owners: OwnersFile | None = None
    journal: list[str] = field(default_factory=list)

    def _freeze_gate(
        self, request: PushRequest
    ) -> GateVerdict:
        try:
            verdict = self.board.check_landing(
                request.branch, request.submitter
            )
            return GateVerdict("freeze", verdict, False)
        except Conflict as refusal:
            return GateVerdict("freeze", str(refusal), True)

    def _force_gate(
        self, request: PushRequest
    ) -> GateVerdict:
        if not request.force:
            return GateVerdict(
                "force", "not requested", False
            )
        try:
            verdict = self.guard.check_force(request.branch)
            return GateVerdict("force", verdict, False)
        except Invalid as refusal:
            return GateVerdict("force", str(refusal), True)

    def _review_gate(
        self, request: PushRequest
    ) -> GateVerdict:
        joined = "\n".join(request.messages)
        try:
            verdict = self.guard.check_landing(
                request.branch, joined
            )
            return GateVerdict("reviews", verdict, False)
        except Invalid as refusal:
            return GateVerdict(
                "reviews", str(refusal), True
            )

    def _owners_gate(
        self, request: PushRequest
    ) -> GateVerdict:
        if self.owners is None:
            return GateVerdict(
                "owners",
                "no owners file configured; routing "
                "skipped",
                False,
            )
        routed = self.owners.route(
            list(request.touched_paths)
        )
        if routed["unclaimed"]:
            orphans = ", ".join(routed["unclaimed"])
            return GateVerdict(
                "owners",
                f"unowned path(s): {orphans}; landing "
                "unowned paths is how orphans breed",
                True,
            )
        reviewers = ", ".join(routed["reviewers"])
        return GateVerdict(
            "owners",
            f"all {len(request.touched_paths)} path(s) "
            f"claimed; route to {reviewers}",
            False,
        )

    def _message_gate(
        self, request: PushRequest
    ) -> GateVerdict:
        findings = sum(
            len(lint_message(message))
            for message in request.messages
        )
        return GateVerdict(
            "message",
            f"{len(request.messages)} message(s), "
            f"{findings} lint finding(s); graded, not "
            "blocked",
            False,
        )

    def receive(self, request: PushRequest) -> str:
        verdicts = [
            self._freeze_gate(request),
            self._force_gate(request),
            self._review_gate(request),
            self._owners_gate(request),
            self._message_gate(request),
        ]
        hard = [
            verdict
            for verdict in verdicts
            if verdict.hard_failure
        ]
        if hard:
            headline = (
                f"push of {request.branch} by "
                f"{request.submitter}: REFUSED, "
                f"{len(hard)} hard failure(s)"
            )
        else:
            headline = (
                f"push of {request.branch} by "
                f"{request.submitter}: ACCEPTED"
            )
        lines = [headline]
        lines.extend(
            verdict.line() for verdict in verdicts
        )
        lines.append(
            "every gate spoke; whatever needs fixing, "
            "the trip back is one"
        )
        page = "\n".join(lines)
        self.journal.append(headline)
        return page
