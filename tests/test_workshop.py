from __future__ import annotations

from keel.organs import roster
from keel.voyages import names
from keel.witnesses import registry


class TestTheWorkshopStands:
    def test_the_registries_agree_with_the_filesystem(
        self,
    ):
        organs = roster()
        voyages = names()
        witnesses = registry.WITNESSES
        assert len(organs) >= 120
        assert len(voyages) == 13
        assert len(witnesses) == 18

    def test_no_witness_is_broken_at_close(self):
        assert registry.broken() == []

    def test_every_registry_name_is_unique(self):
        organ_names = [
            name for name, _headline in roster()
        ]
        assert len(organ_names) == len(
            set(organ_names)
        )
        assert len(names()) == len(set(names()))
