"""The colophon: the closing page a finished workshop prints about itself.

Books end with a colophon, the note on how the thing was
made, and this workshop can print its own because every
number in it is computed by an organ built here: the organ
count from the registry that reads docstrings, the voyage
count from the manifest walk, the witness roster with its
broken count from the measurements run fresh, and the sea
trial's own closing line, run again for the occasion
because a colophon that quotes yesterday's trial is a
brochure. The page states the workshop's three habits in
one line each, refusals that explain themselves, guesses
corrected by measurement and kept, and receipts for
everything loud, since a colophon is where a book admits
what it believes. It ends the only way this workshop
ends anything, with the numbers said plainly and nothing
promised beyond them.
"""

from __future__ import annotations

from keel.organs import roster
from keel.seatrial import run_trial
from keel.voyages import names
from keel.witnesses import registry


def page() -> str:
    testimonies = registry.all_testimonies()
    broken = sum(
        1 for held in testimonies if not held.holds
    )
    trial_close = run_trial().splitlines()[-1]
    lines = [
        "colophon:",
        f"  {len(roster())} organ(s), each opening "
        "with its own sentence",
        f"  {len(names())} voyage(s), each a day "
        "someone has actually had",
        f"  {len(testimonies)} witness(es), "
        f"{broken} broken, measured fresh for this "
        "page",
        f"  {trial_close}",
        "the habits: refusals that explain "
        "themselves; guesses corrected by "
        "measurement and kept; receipts for "
        "everything loud",
        "numbers said plainly, nothing promised "
        "beyond them",
    ]
    return "\n".join(lines)
