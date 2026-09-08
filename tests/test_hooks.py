from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.hooks import (
    HookRunner,
    message_says_something,
    no_debug_droppings,
    no_giant_files,
)

CLEAN = {"app.py": b"def main(): pass"}


def gauntlet() -> HookRunner:
    runner = HookRunner()
    runner.register("droppings", no_debug_droppings)
    runner.register("message", message_says_something)
    runner.register("giants", no_giant_files)
    return runner


class TestTheGauntlet:
    def test_the_satisfied_gate_opens(self):
        verdict = gauntlet().run(
            CLEAN, "a perfectly reasonable subject"
        )
        assert verdict == (
            "3 guard(s) satisfied; the gate opens"
        )

    def test_the_first_rejection_names_the_unheard(self):
        runner = gauntlet()
        with pytest.raises(Invalid) as caught:
            runner.run(
                {"app.py": b"breakpoint()"},
                "a perfectly reasonable subject",
            )
        message = str(caught.value)
        assert message.startswith("rejected by droppings")
        assert "2 guard(s) unheard (message, giants)" in message

    def test_two_guards_cannot_share_a_name(self):
        runner = gauntlet()
        with pytest.raises(Invalid) as caught:
            runner.register("giants", no_giant_files)
        assert "answer for each other's mistakes" in str(
            caught.value
        )

    def test_a_broken_guard_fails_loudly(self):
        runner = HookRunner()

        def unstable(_files, _message):
            raise RuntimeError("guard crashed")

        runner.register("flaky", unstable)
        with pytest.raises(Invalid) as caught:
            runner.run(CLEAN, "a perfectly reasonable subject")
        assert "waving it through" in str(caught.value)


class TestTheStockGuards:
    def test_short_subjects_are_refused_a_sentence(self):
        passed, reason = message_says_something(CLEAN, "wip")
        assert not passed
        assert "history deserves a sentence" in reason

    def test_long_subjects_belong_in_the_body(self):
        passed, reason = message_says_something(
            CLEAN, "x" * 80
        )
        assert not passed
        assert "belongs in the body" in reason

    def test_giants_are_sent_to_the_pointer_store(self):
        passed, reason = no_giant_files(
            {"blob.bin": b"x" * 100_001}, "m"
        )
        assert not passed
        assert "a pointer store, not a commit" in reason
