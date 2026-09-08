from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.rerere import Recorder, conflict_key

BASE = b"shared\ncore"
OURS = b"LEFT\ncore"
THEIRS = b"RIGHT\ncore"
HAND = b"BOTH\ncore"


def seasoned() -> Recorder:
    recorder = Recorder()
    recorder.record(BASE, OURS, THEIRS, HAND)
    return recorder


class TestRecording:
    def test_the_same_collision_replays_with_a_label(self):
        recorder = seasoned()
        replay = recorder.replay(BASE, OURS, THEIRS)
        assert replay is not None
        resolution, receipt = replay
        assert resolution == HAND
        assert receipt.startswith("REPLAYED recording")
        assert "the day it first lies" in receipt

    def test_the_unseen_collision_stays_a_human_question(self):
        recorder = seasoned()
        assert recorder.replay(BASE, OURS, b"OTHER\ncore") is (
            None
        )

    def test_an_empty_resolution_is_a_tree_decision(self):
        with pytest.raises(Invalid) as caught:
            Recorder().record(BASE, OURS, THEIRS, b"  ")
        assert "decided at the tree" in str(caught.value)

    def test_side_takes_are_worth_not_retyping(self):
        recorder = Recorder()
        verdict = recorder.record(BASE, OURS, THEIRS, OURS)
        assert "not retyping" in verdict
        replay = recorder.replay(BASE, OURS, THEIRS)
        assert replay is not None and replay[0] == OURS


class TestTheKey:
    def test_all_three_sides_are_in_the_key(self):
        recorder = Recorder()
        assert recorder.different_base_is_a_different_question(
            BASE, b"other base", OURS, THEIRS
        )
        assert conflict_key(BASE, OURS, THEIRS) != (
            conflict_key(BASE, THEIRS, OURS)
        )

    def test_role_order_matters_because_questions_do(self):
        recorder = seasoned()
        assert recorder.replay(BASE, THEIRS, OURS) is None


class TestForgetting:
    def test_forgetting_reopens_the_question(self):
        recorder = seasoned()
        verdict = recorder.forget(BASE, OURS, THEIRS)
        assert "asks a human again" in verdict
        assert recorder.replay(BASE, OURS, THEIRS) is None

    def test_forgetting_the_unrecorded_is_already_done(self):
        with pytest.raises(Invalid):
            Recorder().forget(BASE, OURS, THEIRS)

    def test_the_ledger_counts_what_was_not_retyped(self):
        recorder = seasoned()
        recorder.replay(BASE, OURS, THEIRS)
        recorder.replay(BASE, OURS, THEIRS)
        assert recorder.ledger() == (
            "1 recording(s), 2 replay(s); every replay is a "
            "hand-resolution not retyped"
        )
