# The credential-shaped strings in this file are synthetic fixtures. They exist
# to give the scanner something to match and they authenticate against nothing.
# No real password, key, token, or personal data appears anywhere in this file.
from __future__ import annotations

import pytest

from keel.departures import Departures
from keel.errors import Conflict
from keel.licensecheck import LicenseAuditor

HEADER = (
    "# Copyright Keelworks\n"
    "# Licensed under the Harbor License v1\n"
)

CLEAN = {
    "src/app.py": HEADER.encode() + b"x = 1\n",
    "docs/notes.md": b"plain prose here\n",
}


def lounge() -> Departures:
    auditor = LicenseAuditor()
    auditor.declare(HEADER)
    return Departures(license_auditor=auditor)


class TestClearance:
    def test_a_clean_shipment_departs_with_a_manifest(
        self,
    ):
        page = lounge().clear(dict(CLEAN))
        assert page.startswith(
            "cleared for departure: 2 file(s)"
        )
        assert (
            "secrets: [ok] nothing secret-shaped "
            "boards"
        ) in page
        assert (
            "portability: [ok] every path travels well"
        ) in page
        assert "license: [ok]" in page
        assert "ordered by blast radius" in page

    def test_secrets_and_collisions_hold_the_flight(
        self,
    ):
        files = dict(CLEAN)
        files["conf.ini"] = b"password=hunter2\n"
        files["src/App.py"] = b"case twin\n"
        with pytest.raises(Conflict) as caught:
            lounge().clear(files)
        page = str(caught.value)
        assert (
            "departure denied: 2 gate(s) hold "
            "(secrets, portability)"
        ) in page
        assert "a leak is forever" in page
        assert "will not survive the trip" in page
        assert "hunter2" not in page

    def test_the_license_gate_never_holds_alone(self):
        files = {
            "src/bare.py": b"x = 1\n",
            "docs/notes.md": b"plain prose here\n",
        }
        page = lounge().clear(files)
        assert page.startswith("cleared for departure")
        assert "license: [ok]" in page
        assert "1 absent" in page
        assert "a header is a patch" in page

    def test_an_undeclared_header_is_waved_through(
        self,
    ):
        page = Departures().clear(dict(CLEAN))
        assert (
            "license: [ok] no header declared; waved "
            "through"
        ) in page
