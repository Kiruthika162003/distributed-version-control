from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.mailmap import Identity, Mailmap

ASHA = Identity(name="Asha Rao", email="asha@corp.example")
ASHA_TYPO = Identity(name="asha rao", email="asha@corp.example")
ASHA_OLD = Identity(name="Asha Rao", email="asha@old.example")
BEN = Identity(name="Ben", email="ben@corp.example")


def unified() -> Mailmap:
    mailmap = Mailmap()
    mailmap.map_exact(ASHA_TYPO, ASHA)
    mailmap.map_email("asha@old.example", ASHA)
    return mailmap


class TestResolution:
    def test_exact_beats_email_beats_passthrough(self):
        mailmap = unified()
        assert mailmap.resolve(ASHA_TYPO) == ASHA
        assert mailmap.resolve(ASHA_OLD) == ASHA
        assert mailmap.resolve(BEN) == BEN

    def test_self_mapping_is_a_diary_entry(self):
        with pytest.raises(Invalid):
            Mailmap().map_exact(ASHA, ASHA)

    def test_emails_must_look_like_emails(self):
        with pytest.raises(Invalid):
            Mailmap().map_email("not-an-email", ASHA)


class TestShortlog:
    def test_four_strangers_become_one_engineer(self):
        mailmap = unified()
        authors = [ASHA, ASHA_TYPO, ASHA_OLD, BEN, ASHA]
        log = mailmap.shortlog(authors)
        lines = log.splitlines()
        assert lines[0].startswith("   4  Asha Rao")
        assert lines[1].startswith("   1  Ben")

    def test_the_unmapped_world_still_ranks(self):
        log = Mailmap().shortlog([BEN, BEN, ASHA])
        assert log.splitlines()[0].startswith("   2  Ben")


class TestTheAudit:
    def test_the_unconfirmed_alias_is_a_suspect(self):
        mailmap = unified()
        drive_by = Identity(
            name="A. Rao", email="asha@corp.example"
        )
        suspects = mailmap.audit([drive_by, BEN])
        assert len(suspects) == 1
        assert "nobody has confirmed" in suspects[0]

    def test_mapped_identities_are_not_suspects(self):
        mailmap = unified()
        assert mailmap.audit([ASHA_TYPO, ASHA_OLD]) == []
