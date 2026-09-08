from __future__ import annotations

import pytest

from keel.draft import draft
from keel.errors import Invalid
from keel.repo import Repo

BASE = {
    "src/app.py": b"core\n",
    "docs/guide.md": b"g\n",
}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    return repo


class TestVerbs:
    def test_pure_addition_reads_as_add(self):
        repo = build()
        proposed = dict(
            BASE, **{"src/export.py": b"e\n"}
        )
        page = draft(repo, proposed)
        assert page.startswith(
            "Add src: <say the actual change>"
        )
        assert "adds src/export.py" in page

    def test_pure_edits_read_as_update(self):
        repo = build()
        proposed = dict(
            BASE, **{"src/app.py": b"core\nmore\n"}
        )
        page = draft(repo, proposed)
        assert page.startswith("Update src:")
        assert "edits src/app.py" in page

    def test_a_mix_reads_as_rework_across_territories(
        self,
    ):
        repo = build()
        proposed = {
            "src/app.py": b"core\nmore\n",
            "src/export.py": b"e\n",
        }
        page = draft(repo, proposed)
        assert page.startswith(
            "Rework across docs, src:"
        )
        assert "removes docs/guide.md" in page
        assert "adds src/export.py" in page
        assert "edits src/app.py" in page


class TestTheFloor:
    def test_the_draft_admits_being_a_floor(self):
        repo = build()
        page = draft(
            repo,
            dict(BASE, **{"src/app.py": b"c2\n"}),
        )
        assert (
            "this draft is a floor; replace every "
            "word that is wrong"
        ) in page

    def test_nothing_changed_is_refused(self):
        repo = build()
        with pytest.raises(Invalid) as caught:
            draft(repo, dict(BASE))
        assert "when nothing happened" in str(
            caught.value
        )
