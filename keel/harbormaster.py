"""The harbormaster: three gauntlets, one landing, one signed page.

The gatekeeper judges the social claims, customs the
material ones, departures the content itself, and the
harbormaster is the office where a landing meets all three
at once, because a submitter sent to three buildings learns
to hate the harbor and a harbor with one desk learns
everything in one visit. Each gauntlet keeps its own page
and its own refusals, quoted whole rather than summarized,
the paraphrase rule holding at the top exactly as it holds
below. The verdict is the conjunction and nothing cleverer:
cleared means all three cleared, held means at least one
held with every objection already itemized by the gauntlet
that raised it, and the harbormaster adds exactly one thing
of its own, the closing count of visits saved, because the
argument for one desk is arithmetic and the receipt may as
well show it.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.customs import Customs
from keel.departures import Departures
from keel.errors import Conflict
from keel.gatekeeper import Gatekeeper, PushRequest


@dataclass
class Harbormaster:
    gatekeeper: Gatekeeper
    customs: Customs
    departures: Departures

    def land(
        self,
        request: PushRequest,
        proposed: dict[str, bytes],
    ) -> str:
        pages: list[str] = []
        held = 0

        social = self.gatekeeper.receive(request)
        if "REFUSED" in social.splitlines()[0]:
            held += 1
        pages.append(social)

        try:
            pages.append(
                self.customs.clear(
                    request.submitter, proposed
                )
            )
        except Conflict as refusal:
            held += 1
            pages.append(str(refusal))

        try:
            pages.append(
                self.departures.clear(proposed)
            )
        except Conflict as refusal:
            held += 1
            pages.append(str(refusal))

        if held:
            headline = (
                f"the harbor holds this landing: "
                f"{held} of 3 gauntlet(s) object, "
                "each in its own words below"
            )
        else:
            headline = (
                "the harbor clears this landing: "
                "three gauntlets, one visit"
            )
        closing = (
            "one desk, three buildings saved; the "
            "argument for the office is arithmetic "
            "and the receipt may as well show it"
        )
        page = "\n\n".join(
            [headline, *pages, closing]
        )
        if held:
            raise Conflict(page)
        return page
