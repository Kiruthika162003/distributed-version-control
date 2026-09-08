"""Automated bisect: the oracle is a program, and programs get graded too.

Manual bisect asks a human at every probe; the automated run
plugs in a test command and drives the hunt to its end, and
what it adds beyond the loop is discipline about the oracle
itself: exit verdicts map to good, bad, or skip through an
explicit table rather than truthiness, an oracle that answers
the same commit differently across reruns is reported as
untrustworthy with both answers shown, and the final verdict
carries the probe transcript so the culprit arrives with its
evidence rather than as a bare address. The transcript is the
part people skip and regret: an automated hunt whose steps
vanish leaves a culprit nobody can defend when the accused
author asks, reasonably, why me.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from keel.bisect import Bisect
from keel.commits import CommitGraph
from keel.errors import Invalid

Oracle = Callable[[str], int]

EXIT_GOOD = 0
EXIT_SKIP = 125


@dataclass
class AutoBisect:
    graph: CommitGraph
    oracle: Oracle
    transcript: list[str] = field(default_factory=list)
    answers: dict[str, int] = field(default_factory=dict)

    def _verdict_for(self, address: str) -> str:
        code = self.oracle(address)
        if address in self.answers and (
            self.answers[address] != code
        ):
            raise Invalid(
                f"the oracle answered {address[:8]} with "
                f"{self.answers[address]} and then {code}; "
                "an oracle that changes its answer is "
                "untrustworthy, and the hunt stops before it "
                "launders that into a verdict"
            )
        self.answers[address] = code
        if code == EXIT_GOOD:
            return "good"
        if code == EXIT_SKIP:
            return "skip"
        return "bad"

    def run(self, good: str, bad: str) -> str:
        hunt = Bisect(graph=self.graph, good=good, bad=bad)
        self.transcript.extend(hunt.log)
        while True:
            probe = hunt.next_probe()
            if probe is None:
                break
            verdict = self._verdict_for(probe)
            self.transcript.append(
                f"oracle: {probe[:8]} -> {verdict} "
                f"(exit {self.answers[probe]})"
            )
            hunt.verdict(probe, verdict)
            self.transcript.append(hunt.log[-1])
        culprit = hunt.culprit()
        self.transcript.append(hunt.log[-1])
        return culprit

    def evidence(self, culprit: str) -> str:
        lines = [
            f"culprit {culprit[:8]} arrives with its "
            f"evidence, {len(self.transcript)} transcript "
            "line(s):"
        ]
        lines.extend(f"  {line}" for line in self.transcript)
        lines.append(
            "when the accused author asks why me, this is "
            "the answer"
        )
        return "\n".join(lines)
