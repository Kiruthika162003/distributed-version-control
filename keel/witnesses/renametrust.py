"""The rename detector graded on a corpus with a planted impostor.

Six files move in one commit: three renamed byte-identical,
two renamed with small edits, and one deleted while an
unrelated file of similar length appears, the impostor pair
that similarity scoring is tempted to marry. The drill runs
detection and grades the columns: the three exact renames
match at similarity 1.0 for the price of a set intersection,
the two edited renames clear the similarity floor and are
reported with their scores, and the impostor pair correctly
falls below the floor and lands as one delete plus one add,
because a detector that marries strangers rewrites blame
across two unrelated histories, which is worse than missing
a rename. The floor earns its value here: detection is a
bet, the floor is the stake, and this corpus is the table.
"""

from __future__ import annotations

from keel.renames import detect_renames
from keel.witnesses.finding import Testimony

OLD_FILES = {
    "src/alpha.py": b"alpha body\n" * 12,
    "src/beta.py": b"beta body\n" * 12,
    "src/gamma.py": b"gamma body\n" * 12,
    "src/edit_one.py": b"line\n" * 20,
    "src/edit_two.py": b"row\n" * 20,
    "src/doomed.py": b"doomed content that vanishes\n" * 4,
}
NEW_FILES = {
    "lib/alpha.py": b"alpha body\n" * 12,
    "lib/beta.py": b"beta body\n" * 12,
    "lib/gamma.py": b"gamma body\n" * 12,
    "lib/edit_one.py": b"line\n" * 19 + b"changed\n",
    "lib/edit_two.py": b"row\n" * 19 + b"altered\n",
    "src/impostor.py": b"completely different words\n" * 4,
}


def run() -> Testimony:
    renames, deleted, added = detect_renames(
        OLD_FILES, NEW_FILES
    )
    exact = [
        pair for pair in renames if pair.similarity == 1.0
    ]
    fuzzy = [
        pair for pair in renames if pair.similarity < 1.0
    ]
    impostor_married = any(
        "doomed" in pair.old_path
        and "impostor" in pair.new_path
        for pair in renames
    )
    numbers = {
        "exact_renames": len(exact),
        "fuzzy_renames": len(fuzzy),
        "fuzzy_scores": tuple(
            round(pair.similarity, 2) for pair in fuzzy
        ),
        "impostor_married": impostor_married,
        "deletes": len(deleted),
        "adds": len(added),
    }
    holds = (
        numbers["exact_renames"] == 3
        and numbers["fuzzy_renames"] == 2
        and not numbers["impostor_married"]
        and numbers["deletes"] == 1
        and numbers["adds"] == 1
    )
    return Testimony(
        witness="renametrust",
        claim=(
            "three exact renames match for the price of a "
            "set intersection, two edited renames clear the "
            "floor with their scores shown, and the impostor "
            "pair stays divorced, because a detector that "
            "marries strangers rewrites blame across two "
            "unrelated histories"
        ),
        numbers=numbers,
        holds=holds,
    )
