from __future__ import annotations

from keel.repo import Repo
from keel.tagaudit import audit
from keel.tags import TagStore


def history(count: int) -> tuple[Repo, list[str]]:
    repo = Repo.init()
    text = b""
    addresses = []
    for step in range(count):
        text += f"{step}\n".encode()
        commit = repo.commit(
            {"log.txt": text}, f"step {step}"
        )
        addresses.append(commit.address)
    return repo, addresses


class TestShapes:
    def test_freeform_names_are_filed_not_flagged(self):
        repo, addresses = history(2)
        tags = TagStore(graph=repo.graph)
        tags.place("v1.0", addresses[0], "cut")
        tags.place(
            "project-alpha", addresses[1], "codename"
        )
        page = audit(repo, tags)
        assert page.startswith(
            "1 versioned tag(s), 1 free-form"
        )
        assert (
            "free-form: project-alpha; not wrong, "
            "not sortable"
        ) in page


class TestOrder:
    def test_the_anachronism_is_named(self):
        repo, addresses = history(3)
        tags = TagStore(graph=repo.graph)
        tags.place("v1.9", addresses[2], "late cut")
        tags.place("v2.0", addresses[0], "early cut")
        page = audit(repo, tags)
        assert (
            "anachronism: v2.0 seals an older commit"
        ) in page
        assert "quietly lied to" in page

    def test_a_clean_line_reads_clean(self):
        repo, addresses = history(3)
        tags = TagStore(graph=repo.graph)
        tags.place("v1.0", addresses[0], "one")
        tags.place("v1.1", addresses[1], "two")
        tags.place("v2.0", addresses[2], "three")
        page = audit(repo, tags)
        assert (
            "the line reads clean; versions sort, "
            "seals agree with time"
        ) in page


class TestGaps:
    def test_missing_majors_are_asked_about(self):
        repo, addresses = history(3)
        tags = TagStore(graph=repo.graph)
        tags.place("v1.0", addresses[0], "one")
        tags.place("v3.0", addresses[2], "three")
        page = audit(repo, tags)
        assert "missing major(s): 2" in page
        assert (
            "asks rather than concludes"
        ) in page
