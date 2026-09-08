from __future__ import annotations

import pytest

from keel.changelog import changelog_between, render_changelog
from keel.errors import Invalid
from keel.repo import Repo

BASE = {"a.txt": b"v0"}


def released() -> tuple[Repo, str, str]:
    repo = Repo.init()
    old = repo.commit(dict(BASE), "base").address
    repo.commit(
        dict(BASE, **{"a.txt": b"v1"}),
        "feat: teach the parser ranges",
    )
    repo.commit(
        dict(BASE, **{"a.txt": b"v2"}),
        "fix: stop the counter skipping on wrap",
    )
    repo.commit(
        dict(BASE, **{"a.txt": b"v3"}),
        "breaking: rename the config key",
    )
    new = repo.commit(
        dict(BASE, **{"a.txt": b"v4"}),
        "tidy the imports",
    ).address
    return repo, old, new


class TestClassification:
    def test_prefixes_route_to_the_expected_sections(self):
        repo, old, new = released()
        sections = changelog_between(repo, old, new)
        assert len(sections["features"]) == 1
        assert len(sections["fixes"]) == 1
        assert len(sections["breaking"]) == 1
        assert len(sections["uncategorized"]) == 1

    def test_prefixes_strip_but_addresses_stay(self):
        repo, old, new = released()
        sections = changelog_between(repo, old, new)
        entry = sections["features"][0]
        assert entry.startswith("teach the parser ranges (")
        assert entry.endswith(")")

    def test_an_empty_range_is_a_shrug_with_headings(self):
        repo, old, _ = released()
        with pytest.raises(Invalid):
            changelog_between(repo, old, old)


class TestRendering:
    def test_breaking_is_never_buried(self):
        repo, old, new = released()
        page = render_changelog(repo, old, new, "v2.0")
        lines = page.splitlines()
        breaking_index = lines.index(
            "## Breaking changes, never buried"
        )
        features_index = lines.index("## Features")
        assert breaking_index < features_index

    def test_the_uncategorized_is_shown_not_dropped(self):
        repo, old, new = released()
        page = render_changelog(repo, old, new, "v2.0")
        assert "shown rather than dropped" in page
        assert "tidy the imports" in page

    def test_the_draft_admits_being_a_draft(self):
        repo, old, new = released()
        assert "the human edits prose, not facts" in (
            render_changelog(repo, old, new, "v2.0")
        )
