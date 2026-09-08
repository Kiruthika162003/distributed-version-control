from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.repo import Repo
from keel.scaffold import found


class TestFounding:
    def test_the_first_commit_reads_as_a_plan(self):
        repo = Repo.init()
        commit, receipt = found(
            repo,
            "harborworks",
            "A small tool for honest harbors.",
        )
        assert receipt.startswith(
            "harborworks founded at"
        )
        assert (
            "laid down .ignore, README.md"
        ) in receipt
        files = repo.head_files()
        assert files["README.md"].startswith(
            b"# harborworks\n"
        )
        assert b"__pycache__/" in files[".ignore"]
        assert commit.message == "found harborworks"

    def test_the_license_anchor_satisfies_the_auditor(
        self,
    ):
        repo = Repo.init()
        header = (
            "# Copyright Keelworks\n"
            "# Licensed under the Harbor License v1"
        )
        found(
            repo,
            "harborworks",
            "A small tool.",
            license_header=header,
        )
        assert b"Harbor License v1" in (
            repo.head_files()["LICENSE"]
        )

    def test_retrofitting_is_refused(self):
        repo = Repo.init()
        repo.commit({"app.py": b"x\n"}, "existing")
        with pytest.raises(Invalid) as caught:
            found(repo, "late", "Too late.")
        assert "different job with different risks" in (
            str(caught.value)
        )

    def test_the_nameless_and_the_silent_are_refused(
        self,
    ):
        with pytest.raises(Invalid):
            found(Repo.init(), "  ", "A sentence.")
        with pytest.raises(Invalid) as caught:
            found(Repo.init(), "named", "   ")
        assert "teaches nothing" in str(caught.value)
