"""Branch naming policy: the namespace is a shared kitchen, label your jars.

Branch names are the only documentation everyone reads, so
the policy makes them carry their one fact: what kind of
work lives there. Names must start with a declared category
prefix, feature slash, fix slash, release slash, and the
rest must be a real slug, lowercase with hyphens, because
BRANCH_FINAL_v2_REAL is a name that documents panic. The
grandfather list exists because policies arrive at
repositories that already have residents, and renaming a
branch someone is standing on costs more than tolerating
its name: grandfathered names pass with a note, new names
meet the full rule, and the audit tells the difference
loudly so the list shrinks instead of growing. Release
names get one extra check, the version segment must look
like a version, since release slash soon is a promise
wearing a category.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from keel.errors import Invalid
from keel.repo import Repo

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VERSION = re.compile(r"^\d+\.\d+(\.\d+)?$")


@dataclass
class NamingPolicy:
    categories: tuple[str, ...] = (
        "feature",
        "fix",
        "release",
    )
    exempt: tuple[str, ...] = ("main",)
    grandfathered: set[str] = field(default_factory=set)

    def check(self, name: str) -> str:
        if name in self.exempt:
            return f"{name}: exempt by charter"
        if name in self.grandfathered:
            return (
                f"{name}: grandfathered; passes with a "
                "note, not a blessing"
            )
        category, slash, slug = name.partition("/")
        if not slash:
            raise Invalid(
                f"{name}: no category; the namespace is "
                "a shared kitchen, label your jars with "
                f"one of {', '.join(self.categories)}"
            )
        if category not in self.categories:
            raise Invalid(
                f"{name}: {category!r} is not a "
                f"category; the shelf holds "
                f"{', '.join(self.categories)}"
            )
        if category == "release":
            if not VERSION.match(slug):
                raise Invalid(
                    f"{name}: a release names a "
                    "version, and release/soon is a "
                    "promise wearing a category"
                )
            return f"{name}: a labeled jar"
        if not SLUG.match(slug):
            raise Invalid(
                f"{name}: {slug!r} is not a slug; "
                "lowercase and hyphens, because "
                "BRANCH_FINAL_v2_REAL documents panic"
            )
        return f"{name}: a labeled jar"

    def grandfather(self, name: str) -> str:
        try:
            self.check(name)
        except Invalid:
            self.grandfathered.add(name)
            return (
                f"{name} grandfathered; tolerated, "
                "not endorsed"
            )
        raise Invalid(
            f"{name} already passes; grandfathering "
            "the compliant pads the list that should "
            "shrink"
        )

    def audit(self, repo: Repo) -> str:
        passing = []
        tolerated = []
        failing = []
        for name in sorted(repo.refs.branches):
            try:
                verdict = self.check(name)
            except Invalid as refusal:
                failing.append(f"  {refusal}")
                continue
            if "grandfathered" in verdict:
                tolerated.append(f"  {verdict}")
            else:
                passing.append(f"  {verdict}")
        lines = [
            f"{len(passing)} labeled, "
            f"{len(tolerated)} tolerated, "
            f"{len(failing)} unlabeled"
        ]
        lines.extend(passing)
        lines.extend(tolerated)
        lines.extend(failing)
        if tolerated:
            lines.append(
                "the grandfather list should shrink; "
                "check whether anyone still stands on "
                "those branches"
            )
        return "\n".join(lines)
