from __future__ import annotations

import pytest

from keel.archive import Archive, export, release_checksum
from keel.errors import Corrupt, Invalid
from keel.repo import Repo

FILES = {
    "src/main.py": b"print(1)",
    "README": b"docs",
}


def released() -> tuple[Repo, str]:
    repo = Repo.init()
    commit = repo.commit(dict(FILES), "release")
    return repo, commit.address


class TestDeterminism:
    def test_the_same_commit_exports_the_same_bytes(self):
        repo, address = released()
        first = export(repo, address)
        second = export(repo, address)
        assert first.archive_digest() == (
            second.archive_digest()
        )

    def test_paths_sort_regardless_of_insertion(self):
        repo, address = released()
        archive = export(repo, address)
        paths = [path for path, _ in archive.entries]
        assert paths == sorted(paths)

    def test_the_prefix_wraps_the_export(self):
        repo, address = released()
        archive = export(repo, address, prefix="proj-1.0")
        assert archive.entries[0][0].startswith("proj-1.0/")

    def test_an_absolute_prefix_is_refused(self):
        repo, address = released()
        with pytest.raises(Invalid):
            export(repo, address, prefix="/opt/proj")


class TestVerification:
    def test_the_intact_archive_verifies_against_its_seal(self):
        repo, address = released()
        archive = export(repo, address)
        sealed = archive.manifest()
        verdict = archive.verify_against(sealed)
        assert "verified against the sealed manifest" in verdict
        assert "its own tampering" in verdict

    def test_truncation_fails_before_the_build(self):
        repo, address = released()
        archive = export(repo, address)
        sealed = archive.manifest()
        truncated = Archive(
            entries=tuple(
                (path, content[:2])
                for path, content in archive.entries
            )
        )
        with pytest.raises(Corrupt) as caught:
            truncated.verify_against(sealed)
        assert "before it is unpacked into a build" in str(
            caught.value
        )

    def test_a_swapped_file_list_travels_badly(self):
        repo, address = released()
        archive = export(repo, address)
        sealed = archive.manifest()
        renamed = Archive(
            entries=(
                ("sneaky.py", archive.entries[0][1]),
                archive.entries[1],
            )
        )
        with pytest.raises(Corrupt) as caught:
            renamed.verify_against(sealed)
        assert "one of them traveled badly" in str(caught.value)

    def test_the_checksum_line_makes_the_promise(self):
        repo, address = released()
        line = release_checksum(repo, address)
        assert "any machine in any decade" in line
