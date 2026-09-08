from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.projects import Atlas
from keel.repo import Repo


def build() -> tuple[Repo, Atlas, list[str]]:
    repo = Repo.init()
    first = repo.commit(
        {
            "web/app.py": b"web\n",
            "api/server.py": b"api\n",
            "README.md": b"hello\n",
        },
        "found the town",
    )
    second = repo.commit(
        {
            "web/app.py": b"web\nmore\n",
            "api/server.py": b"api\n",
            "README.md": b"hello\n",
        },
        "web only",
    )
    third = repo.commit(
        {
            "web/app.py": b"web\nmore\n",
            "api/server.py": b"api\nmore\n",
            "README.md": b"hello\nupdated\n",
        },
        "api and the commons",
    )
    atlas = Atlas()
    atlas.claim("web", "web/")
    atlas.claim("api", "api/")
    return (
        repo,
        atlas,
        [first.address, second.address, third.address],
    )


class TestTheAtlas:
    def test_nesting_claims_are_refused(self):
        _repo, atlas, _addresses = build()
        with pytest.raises(Invalid) as caught:
            atlas.claim("webdeep", "web/components/")
        assert "a lie in one direction" in str(
            caught.value
        )

    def test_the_commons_cannot_be_claimed(self):
        atlas = Atlas()
        with pytest.raises(Invalid) as caught:
            atlas.claim("commons", "misc/")
        assert "hides who sweeps" in str(caught.value)

    def test_a_prefix_ends_with_a_slash(self):
        atlas = Atlas()
        with pytest.raises(Invalid):
            atlas.claim("web", "web")


class TestTouches:
    def test_a_commit_names_its_projects(self):
        repo, atlas, addresses = build()
        assert atlas.checks_for(repo, addresses[1]) == [
            "web"
        ]
        assert atlas.checks_for(repo, addresses[2]) == [
            "api",
            "commons",
        ]

    def test_the_commons_warning_rides_the_touch_line(
        self,
    ):
        repo, atlas, addresses = build()
        line = atlas.touches(repo, addresses[2])
        assert "touches api, commons" in line
        assert "gets the outage" in line
        clean = atlas.touches(repo, addresses[1])
        assert "outage" not in clean


class TestProjectLogs:
    def test_each_project_reads_its_own_history(self):
        repo, atlas, addresses = build()
        tip = addresses[2]
        web_log = atlas.project_log(repo, tip, "web")
        assert [c.address for c in web_log] == [
            addresses[1],
            addresses[0],
        ]
        api_log = atlas.project_log(repo, tip, "api")
        assert [c.address for c in api_log] == [
            addresses[2],
            addresses[0],
        ]

    def test_the_commons_has_a_log_too(self):
        repo, atlas, addresses = build()
        commons_log = atlas.project_log(
            repo, addresses[2], "commons"
        )
        assert [c.address for c in commons_log] == [
            addresses[2],
            addresses[0],
        ]

    def test_a_stranger_project_gets_the_atlas(self):
        repo, atlas, addresses = build()
        with pytest.raises(Missing) as caught:
            atlas.project_log(repo, addresses[2], "cli")
        assert "api, web" in str(caught.value)


class TestTheFloorPlan:
    def test_counts_and_the_sweeping_reminder(self):
        repo, atlas, addresses = build()
        page = atlas.floor_plan(repo, addresses[2])
        assert "2 project(s), 3 file(s):" in page
        assert "api: 1 file(s)" in page
        assert "commons: 1 file(s)" in page
        assert "somebody sweeps it or nobody does" in (
            page
        )
