"""Protected branches: some names are load-bearing, and the rules say which.

Every repository has branches whose tips other systems stand
on, deploys, releases, the default branch itself, and
protection is the difference between a convention and a
guarantee. A protection rule binds a branch pattern to its
restrictions: no deletion, no forced movement, and optionally
a required review count that landing commits must carry as a
trailer, checked at the gate rather than trusted from the
description. The gate reports which rule fired and which
restriction, because a refusal that just says protected
sends the developer to find an admin when the answer was in
the rule all along. Unprotected branches stay fast and
loose by design, since protection everywhere is friction
everywhere, and friction everywhere teaches people to work
in forks where no rules reach at all.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from keel.errors import Invalid
from keel.trailers import query


@dataclass(frozen=True)
class Protection:
    pattern: str
    no_delete: bool = True
    no_force: bool = True
    required_reviews: int = 0


@dataclass
class BranchGuard:
    rules: list[Protection] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)

    def protect(self, rule: Protection) -> str:
        self.rules.append(rule)
        return (
            f"{rule.pattern} protected; convention becomes "
            "guarantee"
        )

    def _rule_for(self, branch: str) -> Protection | None:
        for rule in self.rules:
            if fnmatch.fnmatch(branch, rule.pattern):
                return rule
        return None

    def check_delete(self, branch: str) -> str:
        rule = self._rule_for(branch)
        if rule and rule.no_delete:
            refusal = (
                f"{branch}: deletion refused by rule "
                f"{rule.pattern} (no_delete); other systems "
                "stand on this tip"
            )
            self.refusals.append(refusal)
            raise Invalid(refusal)
        return f"{branch} may be deleted; no rule speaks"

    def check_force(self, branch: str) -> str:
        rule = self._rule_for(branch)
        if rule and rule.no_force:
            refusal = (
                f"{branch}: forced movement refused by rule "
                f"{rule.pattern} (no_force); the rule names "
                "the restriction so nobody hunts an admin"
            )
            self.refusals.append(refusal)
            raise Invalid(refusal)
        return f"{branch} may move freely"

    def check_landing(
        self, branch: str, message: str
    ) -> str:
        rule = self._rule_for(branch)
        if rule is None or rule.required_reviews == 0:
            return f"{branch}: fast and loose by design"
        reviews = len(query(message, "reviewed-by"))
        if reviews < rule.required_reviews:
            refusal = (
                f"{branch}: {reviews} review trailer(s) "
                f"against {rule.required_reviews} required by "
                f"{rule.pattern}; checked at the gate, not "
                "trusted from the description"
            )
            self.refusals.append(refusal)
            raise Invalid(refusal)
        return (
            f"{branch}: {reviews} review(s) satisfy "
            f"{rule.pattern}"
        )
