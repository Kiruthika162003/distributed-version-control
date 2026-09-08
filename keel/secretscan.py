"""Secret scanning: the gate that reads arrivals before history is forever.

A leaked secret in a committed file has a shelf life of
however long anyone might have fetched it, which is why the
expunge tool ends with the advice to rotate; this scanner
exists so that advice is needed less. Three families are
checked with the patterns stated in code: key-shaped
strings, the labeled credentials of the password-equals
kind, and private key headers, which are their own
confession. Every finding names the path, the line, and
the family, never the secret itself, because a report that
quotes the credential is a second leak wearing a badge.
The gate checks proposed files before they become commits,
the only moment removal is still cheap, and a finding at
the gate is a refusal, not advice, since the one thing
cheaper than rotating a leaked secret is refusing to leak
it. False positives get an escape spelled scan-waive in
the line itself, visible in review forever, because a
waiver that lives outside the file outlives its reason.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from keel.errors import Conflict

WAIVER = "scan-waive"

KEY_SHAPED = re.compile(
    r"\b[A-Z0-9]{20,}\b|\b[A-Za-z0-9+/]{40}=?\b"
)
LABELED = re.compile(
    r"(?i)\b(password|passwd|secret|api_key|token)\s*"
    r"[:=]\s*\S+"
)
PEM_HEADER = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
)


@dataclass(frozen=True)
class Finding:
    path: str
    line_number: int
    family: str

    def line(self) -> str:
        return (
            f"  {self.path}:{self.line_number}: "
            f"{self.family}; the secret itself is not "
            "quoted, a report that quotes the "
            "credential is a second leak"
        )


def scan_text(path: str, content: bytes) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = content.decode()
    except UnicodeDecodeError:
        return []
    for number, line in enumerate(
        text.splitlines(), start=1
    ):
        if WAIVER in line:
            continue
        if PEM_HEADER.search(line):
            findings.append(
                Finding(
                    path=path,
                    line_number=number,
                    family=(
                        "private key header, its own "
                        "confession"
                    ),
                )
            )
            continue
        if LABELED.search(line):
            findings.append(
                Finding(
                    path=path,
                    line_number=number,
                    family="labeled credential",
                )
            )
            continue
        if KEY_SHAPED.search(line):
            findings.append(
                Finding(
                    path=path,
                    line_number=number,
                    family="key-shaped string",
                )
            )
    return findings


def scan_files(
    files: dict[str, bytes]
) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(files):
        findings.extend(scan_text(path, files[path]))
    return findings


def gate_arrivals(files: dict[str, bytes]) -> str:
    findings = scan_files(files)
    if findings:
        raise Conflict(
            f"{len(findings)} secret-shaped finding(s) "
            "at the gate, where removal is still "
            "cheap:\n"
            + "\n".join(
                finding.line() for finding in findings
            )
            + "\na true false-positive earns a "
            f"{WAIVER} marker in the line itself, "
            "visible in review forever"
        )
    return (
        f"{len(files)} file(s) scanned; nothing "
        "secret-shaped arrived"
    )
