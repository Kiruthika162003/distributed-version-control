from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.licensecheck import LicenseAuditor

HEADER = (
    "# Copyright Keelworks\n"
    "# Licensed under the Harbor License v1\n"
)


def declared() -> LicenseAuditor:
    auditor = LicenseAuditor()
    auditor.declare(HEADER)
    return auditor


class TestVerdicts:
    def test_the_exact_header_is_present(self):
        auditor = declared()
        content = HEADER.encode() + b"\ncode = 1\n"
        assert auditor.verdict(content) == "present"

    def test_a_missing_header_is_absent(self):
        auditor = declared()
        assert auditor.verdict(b"code = 1\n") == (
            "absent"
        )

    def test_a_reworded_header_is_mangled(self):
        auditor = declared()
        content = (
            b"# Copyright Keelworks\n"
            b"# Licensed under the Harbor License v2\n"
            b"code = 1\n"
        )
        assert auditor.verdict(content) == "mangled"

    def test_auditing_before_declaring_is_refused(self):
        with pytest.raises(Invalid) as caught:
            LicenseAuditor().verdict(b"code\n")
        assert "approves everything" in str(caught.value)

    def test_an_empty_header_licenses_nothing(self):
        with pytest.raises(Invalid):
            LicenseAuditor().declare("  \n  ")


class TestTheAudit:
    def test_mangled_outranks_absent_in_the_fix_list(
        self,
    ):
        auditor = declared()
        files = {
            "good.py": HEADER.encode() + b"x = 1\n",
            "old.py": (
                b"# Copyright Keelworks\n"
                b"# Licensed under the Harbor "
                b"License v9\nx = 1\n"
            ),
            "bare.py": b"x = 1\n",
            "logo.png": b"\xff\xd8",
            "notes.md": b"prose\n",
        }
        page = auditor.audit(files)
        assert page.startswith(
            "1 present, 1 mangled, 1 absent, "
            "2 out of scope"
        )
        lines = page.splitlines()
        assert lines[1].startswith("  mangled: old.py")
        assert lines[2].startswith("  absent: bare.py")
        assert "under oath" in lines[1]

    def test_a_clean_audit_promises_boredom(self):
        auditor = declared()
        page = auditor.audit(
            {"good.py": HEADER.encode() + b"x = 1\n"}
        )
        assert (
            "diligence week will be boring here"
        ) in page
