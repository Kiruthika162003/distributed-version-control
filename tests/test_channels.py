from __future__ import annotations

import pytest

from keel.channels import Channels
from keel.errors import Invalid, Missing
from keel.repo import Repo


def build() -> tuple[Repo, Channels, list[str]]:
    repo = Repo.init()
    addresses = []
    text = b""
    for step in range(4):
        text += f"v{step}\n".encode()
        commit = repo.commit(
            {"app.py": text}, f"version {step}"
        )
        addresses.append(commit.address)
    return repo, Channels(repo=repo), addresses


class TestClimbing:
    def test_the_ladder_climbs_rung_by_rung(self):
        _repo, channels, addresses = build()
        channels.advance(addresses[1])
        assert channels.promote("beta").startswith(
            "beta now at"
        )
        receipt = channels.promote("stable")
        assert "standing on beta" in receipt
        assert channels.held["stable"] == addresses[1]

    def test_the_bottom_rung_advances_not_promotes(self):
        _repo, channels, addresses = build()
        channels.advance(addresses[0])
        with pytest.raises(Invalid) as caught:
            channels.promote("dev")
        assert "it advances, it is not promoted" in str(
            caught.value
        )

    def test_an_empty_rung_ends_the_leap_of_faith(self):
        _repo, channels, _addresses = build()
        with pytest.raises(Invalid) as caught:
            channels.promote("beta")
        assert "ladders exist to end those" in str(
            caught.value
        )

    def test_a_stranger_rung_gets_the_ladder(self):
        _repo, channels, _addresses = build()
        with pytest.raises(Missing) as caught:
            channels.promote("nightly")
        assert "dev -> beta -> stable" in str(
            caught.value
        )

    def test_promoting_in_place_climbs_nothing(self):
        _repo, channels, addresses = build()
        channels.advance(addresses[1])
        channels.promote("beta")
        assert "nothing to climb" in channels.promote(
            "beta"
        )


class TestRewinds:
    def test_even_dev_refuses_to_rewind(self):
        _repo, channels, addresses = build()
        channels.advance(addresses[2])
        with pytest.raises(Invalid) as caught:
            channels.advance(addresses[0])
        assert "signed why" in str(caught.value)

    def test_rollback_demands_its_sentence(self):
        _repo, channels, addresses = build()
        channels.advance(addresses[2])
        with pytest.raises(Invalid):
            channels.rollback("dev", addresses[0], "  ")
        entry = channels.rollback(
            "dev",
            addresses[0],
            "version 2 corrupts saved games",
        )
        assert entry.startswith("ROLLBACK dev:")
        assert "corrupts saved games" in entry
        assert channels.held["dev"] == addresses[0]


class TestTheLag:
    def test_each_rung_counts_its_trail(self):
        _repo, channels, addresses = build()
        channels.advance(addresses[1])
        channels.promote("beta")
        channels.promote("stable")
        channels.advance(addresses[3])
        page = channels.lag_report()
        assert "dev:" in page
        assert "the leading edge" in page
        assert "beta:" in page
        assert "2 commit(s) behind dev" in page
        assert "0 commit(s) behind beta" in page
