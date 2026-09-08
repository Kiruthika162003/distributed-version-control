"""Bisect: a binary search that shows its work at every cut.

Finding the commit that broke something is a search problem
wearing a debugging costume, and the search narrates because
the person running it is making a judgment call at every
step: each probe names the commit under test, the size of the
remaining window, and the probes the halving still owes, so
"how much longer" always has an answer. The first draft
shrank the candidate list in place and the tests caught the
rot immediately: earlier verdicts fell out of the list and
the contradiction check crashed instead of accusing, so the
line is immutable now and only the window bounds move, which
is the design lesson in one sentence: positions are facts and
facts do not reindex. Verdicts contradicting earlier ones are
refused with both named, because a bisect fed inconsistent
answers launders them into a confident accusation of an
innocent commit. Skips step aside without shrinking the
window, and skips crowding the culprit end the hunt with a
range, not a guess.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.commits import CommitGraph
from keel.errors import Invalid


@dataclass
class Bisect:
    graph: CommitGraph
    good: str
    bad: str
    line: list[str] = field(default_factory=list)
    low: int = 0
    high: int = 0
    verdicts: dict[str, str] = field(default_factory=dict)
    probes: int = 0
    log: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.graph.is_ancestor(self.good, self.bad):
            raise Invalid(
                "the good commit must be an ancestor of the "
                "bad one; a bisect across unrelated history "
                "searches nothing"
            )
        collected: list[str] = []
        cursor = self.bad
        while cursor != self.good:
            commit = self.graph.get(cursor)
            if len(commit.parents) != 1:
                raise Invalid(
                    "bisect walks first-parent lines only; a "
                    "merge in the window needs its own hunt"
                )
            collected.append(cursor)
            cursor = commit.parents[0]
        collected.reverse()
        self.line = collected
        self.low = 0
        self.high = len(collected) - 1
        self.log.append(
            f"window of {len(collected)} commit(s) between "
            f"{self.good[:8]} (good) and {self.bad[:8]} (bad); "
            f"about {self._steps_owed()} probe(s) owed"
        )

    def _bounded(self) -> list[str]:
        return self.line[self.low : self.high + 1]

    def _testable_untested(self) -> list[str]:
        return [
            address
            for address in self._bounded()
            if address not in self.verdicts
        ]

    def _steps_owed(self) -> int:
        count = len(self._testable_untested())
        steps = 0
        while count > 1:
            count //= 2
            steps += 1
        return steps

    def next_probe(self) -> str | None:
        untested = self._testable_untested()
        if not untested or len(self._bounded()) <= 1:
            return None
        probe = untested[len(untested) // 2]
        self.log.append(
            f"probing {probe[:8]} "
            f"({self.graph.get(probe).message}); "
            f"{len(untested)} candidate(s) remain, about "
            f"{self._steps_owed()} probe(s) owed"
        )
        return probe

    def verdict(self, address: str, result: str) -> str:
        if result not in ("good", "bad", "skip"):
            raise Invalid(
                f"{result} is not a verdict; good, bad, or skip"
            )
        if address not in self.line:
            raise Invalid(f"{address[:8]} is not in the window")
        position = self.line.index(address)
        if result != "skip":
            for other, other_result in self.verdicts.items():
                if other_result == "skip":
                    continue
                other_position = self.line.index(other)
                contradiction = (
                    result == "good"
                    and other_result == "bad"
                    and other_position < position
                ) or (
                    result == "bad"
                    and other_result == "good"
                    and other_position > position
                )
                if contradiction:
                    raise Invalid(
                        f"{address[:8]} cannot be {result} "
                        f"while {other[:8]} is {other_result}; "
                        "inconsistent answers launder into a "
                        "confident accusation of an innocent "
                        "commit"
                    )
        self.probes += 1
        self.verdicts[address] = result
        if result == "good":
            self.low = max(self.low, position + 1)
        elif result == "bad":
            self.high = min(self.high, position)
        self.log.append(
            f"{address[:8]} is {result}; window now "
            f"{len(self._bounded())}"
        )
        return self.log[-1]

    def culprit(self) -> str:
        bounded = self._bounded()
        if len(bounded) == 1:
            found = bounded[0]
            self.log.append(
                f"culprit: {found[:8]} "
                f"({self.graph.get(found).message}) after "
                f"{self.probes} probe(s)"
            )
            return found
        if self._testable_untested():
            raise Invalid(
                f"{len(bounded)} commit(s) still in the "
                "window; the hunt is not finished"
            )
        skipped = [
            address
            for address in bounded
            if self.verdicts.get(address) == "skip"
        ]
        first = bounded[0][:8]
        last = bounded[-1][:8]
        raise Invalid(
            f"the window narrowed to {first}..{last} with "
            f"{len(skipped)} skip(s) inside; the answer is a "
            "range, not a guess, and the range is what you get"
        )
