"""Corruption planted on purpose, so the physical can prove it finds it.

An fsck that has only ever seen healthy repositories is a
smoke detector that has never met smoke. The drill plants
exactly two injuries in one repository: a blob whose payload
is tampered so the bytes no longer match the address, and a
blob deleted outright so the tree that names it points at
nothing. The physical must find both, and must list the
broken link before the tampered blob, because the report
orders by blast radius and a severed tree entry orphans a
subtree while a corrupt blob breaks one file. A second,
healthy repository gets one unreferenced object dropped into
its store, and the physical must call it dangling exhaust
rather than an error, since a detector that cries wolf over
exhaust teaches operators to skip the physical. Both
measurements came back as guessed: two findings in the
injured repo, links listed first, and one dangling object
reported without alarm in the healthy one.
"""

from __future__ import annotations

from keel.fsck import Physical
from keel.objects import BLOB
from keel.repo import Repo
from keel.witnesses.finding import Testimony


def _injured() -> str:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"app body\n", "lib.py": b"lib body\n"},
        "begin",
    )
    app_blob = repo.store.put(BLOB, b"app body\n")
    lib_blob = repo.store.put(BLOB, b"lib body\n")
    repo.store.objects[app_blob] = (BLOB, b"tampered\n")
    del repo.store.objects[lib_blob]
    return Physical(repo=repo).run()


def _healthy_with_exhaust() -> str:
    repo = Repo.init()
    repo.commit({"app.py": b"app body\n"}, "begin")
    repo.store.put(BLOB, b"unreferenced exhaust\n")
    return Physical(repo=repo).run()


def run() -> Testimony:
    injured_page = _injured()
    healthy_page = _healthy_with_exhaust()
    injured_lines = injured_page.splitlines()
    link_position = next(
        (
            index
            for index, line in enumerate(injured_lines)
            if "points at missing" in line
        ),
        -1,
    )
    corrupt_position = next(
        (
            index
            for index, line in enumerate(injured_lines)
            if "no longer match" in line
        ),
        -1,
    )
    numbers = {
        "findings_planted": 2,
        "findings_reported": (
            2
            if injured_page.startswith("2 finding(s)")
            else 0
        ),
        "links_listed_first": (
            0 < link_position < corrupt_position
        ),
        "healthy_clean": healthy_page.startswith(
            "physical clean"
        ),
        "dangling_reported": "1 dangling" in healthy_page,
    }
    holds = (
        numbers["findings_reported"] == 2
        and numbers["links_listed_first"]
        and numbers["healthy_clean"]
        and numbers["dangling_reported"]
    )
    return Testimony(
        witness="fsckdrill",
        claim=(
            "two injuries planted, two findings reported "
            "with the severed link listed before the "
            "tampered blob, and the healthy repository's "
            "loose object called dangling exhaust rather "
            "than an error"
        ),
        numbers=numbers,
        holds=holds,
    )
