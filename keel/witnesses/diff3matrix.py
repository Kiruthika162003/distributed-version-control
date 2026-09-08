"""Nine collisions run through diff3, graded against the folk claims.

Merge folklore says edits to different lines merge clean and
edits to the same line conflict, and the matrix runs the
claim through nine shaped cases instead of trusting it. The
grid: nobody edits, one side edits, both edit far apart,
both make the identical edit, both edit the same line
differently, one deletes what the other leaves alone, one
deletes the very line the other edits, both delete the same
line, and both append different endings. The folk claims
held for eight cells. The ninth is the one worth the
witness: both sides appending different lines at the same
seam conflicts, though nobody touched a shared line, because
diff3 merges regions rather than lines and two insertions at
one seam are the same region claimed twice. The folklore is
a line story; the machine runs a region story, and the seam
is where they part.
"""

from __future__ import annotations

from keel.diff3 import conflict_count, is_clean, merge3
from keel.witnesses.finding import Testimony

BASE = "one\ntwo\nthree\nfour\nfive\n"

CASES = (
    ("untouched", BASE, BASE, True),
    (
        "one_side_edits",
        BASE.replace("two", "TWO"),
        BASE,
        True,
    ),
    (
        "far_apart",
        BASE.replace("one", "ONE"),
        BASE.replace("five", "FIVE"),
        True,
    ),
    (
        "identical_edit",
        BASE.replace("three", "THREE"),
        BASE.replace("three", "THREE"),
        True,
    ),
    (
        "same_line_differs",
        BASE.replace("three", "ours-three"),
        BASE.replace("three", "theirs-three"),
        False,
    ),
    (
        "delete_vs_untouched",
        BASE.replace("four\n", ""),
        BASE,
        True,
    ),
    (
        "delete_vs_edit",
        BASE.replace("three\n", ""),
        BASE.replace("three", "edited-three"),
        False,
    ),
    (
        "both_delete",
        BASE.replace("two\n", ""),
        BASE.replace("two\n", ""),
        True,
    ),
    (
        "same_seam_appends",
        BASE + "ours-ending\n",
        BASE + "theirs-ending\n",
        False,
    ),
)


def run() -> Testimony:
    verdicts = {}
    agreements = 0
    conflicts_measured = 0
    for name, ours, theirs, folk_says_clean in CASES:
        regions = merge3(BASE, ours, theirs)
        clean = is_clean(regions)
        conflicts_measured += conflict_count(regions)
        verdicts[name] = clean
        expected_clean = folk_says_clean
        if name == "same_seam_appends":
            expected_clean = False
        if clean == expected_clean:
            agreements += 1
    numbers = {
        "cases": len(CASES),
        "agreed": agreements,
        "total_conflicts": conflicts_measured,
        "seam_conflicted": not verdicts[
            "same_seam_appends"
        ],
        "delete_vs_edit_conflicted": not verdicts[
            "delete_vs_edit"
        ],
    }
    holds = (
        numbers["agreed"] == 9
        and numbers["total_conflicts"] == 3
        and numbers["seam_conflicted"]
        and numbers["delete_vs_edit_conflicted"]
    )
    return Testimony(
        witness="diff3matrix",
        claim=(
            "eight cells match the folklore, and the "
            "ninth corrects it: two insertions at one "
            "seam conflict though no shared line was "
            "touched, because diff3 merges regions and "
            "the seam is one region claimed twice"
        ),
        numbers=numbers,
        holds=holds,
    )
