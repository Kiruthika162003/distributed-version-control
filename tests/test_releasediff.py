from __future__ import annotations

from keel.releasediff import manifest_diff
from keel.repo import Repo
from keel.tags import TagStore


def build() -> tuple[Repo, TagStore]:
    repo = Repo.init()
    first = repo.commit(
        {
            "app.py": b"core\n",
            "legacy.py": b"old\n",
            "README": b"hello\n",
        },
        "v1 state",
    )
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", first.address, "first cut")
    second = repo.commit(
        {
            "app.py": b"core\nmore\n",
            "fresh.py": b"new\n",
            "README": b"hello\n",
        },
        "v2 state",
    )
    tags.place("v2.0", second.address, "second cut")
    return repo, tags


class TestTheManifest:
    def test_arrivals_departures_and_changes(self):
        repo, tags = build()
        page = manifest_diff(repo, tags, "v1.0", "v2.0")
        assert page.startswith(
            "shipment v1.0 -> v2.0:"
        )
        assert "enters: fresh.py (4 byte(s))" in page
        assert "leaves: legacy.py" in page
        assert (
            "the customer notices departures before "
            "arrivals"
        ) in page
        assert "changes: app.py (+5 byte(s))" in page
        assert (
            "1 crate(s) untouched, counted and not "
            "listed"
        ) in page

    def test_walking_versus_arriving_is_reconciled(self):
        repo, tags = build()
        page = manifest_diff(repo, tags, "v1.0", "v2.0")
        assert (
            "1 commit(s) of walking, 3 file(s) of "
            "arriving"
        ) in page
        assert "a lot of walking" not in page

    def test_heavy_walking_light_arriving_is_named(self):
        repo, tags = build()
        files = dict(
            repo.files_at(tags.resolve("v2.0"))
        )
        for step in range(8):
            files["app.py"] += f"w{step}\n".encode()
            repo.commit(dict(files), f"walk {step}")
        tags.place(
            "v3.0", repo.refs.current(), "third cut"
        )
        page = manifest_diff(repo, tags, "v2.0", "v3.0")
        assert (
            "8 commit(s) of walking, 1 file(s) of "
            "arriving"
        ) in page
        assert (
            "a lot of walking to arrive nearby"
        ) in page
