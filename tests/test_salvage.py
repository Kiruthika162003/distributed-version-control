from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.salvage import dive, raise_and_commit


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    old = repo.commit(
        {
            "helpers.py": b"the good version\n",
            "app.py": b"core\n",
        },
        "the era of helpers",
    )
    repo.commit(
        {
            "helpers.py": b"a worse rewrite\n",
            "app.py": b"core\n",
        },
        "the regrettable rewrite",
    )
    return repo, old.address


class TestTheDive:
    def test_bytes_come_up_with_their_provenance(self):
        repo, old = build()
        content, provenance = dive(
            repo, old, "helpers.py"
        )
        assert content == b"the good version\n"
        assert provenance.startswith(
            f"salvaged helpers.py from {old[:8]}"
        )
        assert "'the era of helpers'" in provenance

    def test_a_missing_path_gets_the_nearest_names(
        self,
    ):
        repo, old = build()
        with pytest.raises(Missing) as caught:
            dive(repo, old, "utils.py")
        message = str(caught.value)
        assert "was not aboard" in message
        assert "helpers.py" in message
        assert "not an empty net" in message


class TestTheRaise:
    def test_the_recovery_is_itself_history(self):
        repo, old = build()
        receipt = raise_and_commit(
            repo, old, "helpers.py"
        )
        assert "landed as" in receipt
        assert repo.head_files()["helpers.py"] == (
            b"the good version\n"
        )
        assert repo.history()[0].endswith(
            f"salvaged helpers.py from {old[:8]} "
            "('the era of helpers')"
        )

    def test_diving_for_whats_on_deck_is_refused(self):
        repo, old = build()
        raise_and_commit(repo, old, "helpers.py")
        with pytest.raises(Invalid) as caught:
            raise_and_commit(repo, old, "helpers.py")
        assert "already on deck" in str(caught.value)
