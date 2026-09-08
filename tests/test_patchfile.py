from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid
from keel.patchfile import apply_patch, format_patch
from keel.patchid import patch_id
from keel.repo import Repo

BASE = {"app.py": b"one\ntwo", "docs.md": b"start"}


def mailed() -> tuple[Repo, str, str]:
    sender = Repo.init()
    sender.commit(dict(BASE), "base")
    fix = sender.commit(
        dict(BASE, **{"app.py": b"one\nFIXED"}),
        "fix the second line",
    ).address
    return sender, fix, format_patch(sender, fix)


class TestFormatting:
    def test_the_mail_carries_subject_and_pairs(self):
        _, _, mail = mailed()
        assert mail.startswith(
            "Subject: fix the second line"
        )
        assert "Change: app.py" in mail
        assert "Old: one\\ntwo" in mail
        assert "New: one\\nFIXED" in mail

    def test_merges_travel_as_bundles(self):
        sender, _, _ = mailed()
        root = next(
            a
            for a in sender.graph.commits
            if not sender.graph.get(a).parents
        )
        with pytest.raises(Invalid) as caught:
            format_patch(sender, root)
        assert "not letters" in str(caught.value)


class TestApplying:
    def test_the_round_trip_shares_a_patch_identity(self):
        sender, fix, mail = mailed()
        receiver = Repo.init()
        receiver.commit(dict(BASE), "base")
        applied = apply_patch(receiver, mail)
        assert patch_id(receiver, applied.address) == (
            patch_id(sender, fix)
        )
        assert applied.message == "fix the second line"

    def test_the_mismatch_is_named_before_writing(self):
        _, _, mail = mailed()
        receiver = Repo.init()
        receiver.commit(
            dict(BASE, **{"app.py": b"drifted"}), "base"
        )
        with pytest.raises(Conflict) as caught:
            apply_patch(receiver, mail)
        assert "app.py" in str(caught.value)
        assert "nobody can describe" in str(caught.value)

    def test_spam_and_greetings_are_refused(self):
        receiver = Repo.init()
        receiver.commit(dict(BASE), "base")
        with pytest.raises(Invalid):
            apply_patch(receiver, "Change: x\nOld: a\nNew: b")
        with pytest.raises(Invalid):
            apply_patch(receiver, "Subject: hello")
