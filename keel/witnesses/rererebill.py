"""One recorded resolution billed across an integration season.

A long-lived branch meets the same collision at every
integration point, so the drill simulates the season: one
hand-resolution recorded, then five more collisions arrive.
Four are byte-identical twins, base and ours and theirs all
matching, and each replays the recording for free. The fifth
wears the same ours and theirs but stands on a different
base, and the recorder correctly returns nothing, because two
conflicts with the same sides and different bases are
different questions wearing the same clothes, and answering
one with the other is how rerere earns horror stories. The
bill: one resolution typed by a human, four replayed, one
honest miss sent back to a human. The miss is the number
worth staring at, since a recorder without it would have
scored five for five by lying on the fifth.
"""

from __future__ import annotations

from keel.rerere import Recorder
from keel.witnesses.finding import Testimony

BASE = b"core\n"
OTHER_BASE = b"core\nreworked\n"
OURS = b"core\nfeature\n"
THEIRS = b"core\nfixed\n"
RESOLUTION = b"core\nfixed\nfeature\n"


def run() -> Testimony:
    recorder = Recorder()
    recorder.record(BASE, OURS, THEIRS, RESOLUTION)
    replays = 0
    for _integration in range(4):
        replayed = recorder.replay(BASE, OURS, THEIRS)
        if (
            replayed is not None
            and replayed[0] == RESOLUTION
        ):
            replays += 1
    twin_in_different_clothes = recorder.replay(
        OTHER_BASE, OURS, THEIRS
    )
    numbers = {
        "recorded_by_hand": recorder.recordings_made,
        "replayed_free": replays,
        "different_base_missed": (
            twin_in_different_clothes is None
        ),
        "ledger_replays": recorder.replays,
    }
    holds = (
        numbers["recorded_by_hand"] == 1
        and numbers["replayed_free"] == 4
        and numbers["different_base_missed"]
        and numbers["ledger_replays"] == 4
    )
    return Testimony(
        witness="rererebill",
        claim=(
            "one resolution typed by a human, four "
            "byte-identical twins replayed for free, and "
            "the same-sides different-base collision "
            "honestly missed, because a recorder without "
            "the miss would score five for five by lying "
            "on the fifth"
        ),
        numbers=numbers,
        holds=holds,
    )
