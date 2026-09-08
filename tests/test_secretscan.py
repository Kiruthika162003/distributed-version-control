from __future__ import annotations

import pytest

from keel.errors import Conflict
from keel.secretscan import (
    gate_arrivals,
    scan_files,
    scan_text,
)


class TestFamilies:
    def test_a_labeled_credential_is_found(self):
        findings = scan_text(
            "conf.ini", b"password = hunter2\n"
        )
        assert len(findings) == 1
        assert findings[0].family == (
            "labeled credential"
        )
        assert findings[0].line_number == 1

    def test_a_pem_header_is_its_own_confession(self):
        findings = scan_text(
            "key.pem",
            b"-----BEGIN RSA PRIVATE KEY-----\n",
        )
        assert len(findings) == 1
        assert "confession" in findings[0].family

    def test_a_key_shaped_string_is_found(self):
        findings = scan_text(
            "deploy.sh",
            b"export X=AKIA9999FAKEFAKEFAKE9\n",
        )
        assert len(findings) == 1
        assert findings[0].family == (
            "key-shaped string"
        )

    def test_plain_prose_passes(self):
        assert (
            scan_text(
                "notes.md",
                b"the password policy is strict\n"
                b"we rotate keys quarterly\n",
            )
            == []
        )

    def test_binary_content_is_left_alone(self):
        assert (
            scan_text("logo.png", b"\xff\xd8\xff\xe0")
            == []
        )


class TestWaivers:
    def test_the_waiver_lives_in_the_line_itself(self):
        findings = scan_text(
            "docs.md",
            b"password = example-only  # scan-waive\n",
        )
        assert findings == []


class TestTheGate:
    def test_the_report_never_quotes_the_secret(self):
        with pytest.raises(Conflict) as caught:
            gate_arrivals(
                {"conf.ini": b"secret=hunter2\n"}
            )
        message = str(caught.value)
        assert "hunter2" not in message
        assert "conf.ini:1: labeled credential" in (
            message
        )
        assert "scan-waive marker" in message

    def test_a_clean_shipment_is_counted(self):
        receipt = gate_arrivals(
            {"a.md": b"hello\n", "b.md": b"world\n"}
        )
        assert receipt == (
            "2 file(s) scanned; nothing secret-shaped "
            "arrived"
        )

    def test_scan_files_walks_in_path_order(self):
        findings = scan_files(
            {
                "b.ini": b"token: abc123\n",
                "a.pem": (
                    b"-----BEGIN PRIVATE KEY-----\n"
                ),
            }
        )
        assert [f.path for f in findings] == [
            "a.pem",
            "b.ini",
        ]
