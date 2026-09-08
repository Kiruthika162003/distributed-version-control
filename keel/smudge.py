"""Clean and smudge: the repository speaks one dialect, the desk speaks yours.

Line endings are the oldest cross-platform argument in
version control, and the filter pair ends it by giving each
side its own dialect: clean runs on the way into history and
normalizes to bare newlines, smudge runs on the way out and
dresses the text in the desk's convention, so the repository
stores one truth while every machine sees its native form.
The pair must be inverses on the round trip, and the filter
verifies that on every clean, because a filter pair that
drifts turns every checkout-commit cycle into a phantom
diff machine, page-long changes where nobody changed
anything. Binary content is exempted by sniff test and said
so, since normalizing the newlines inside a PNG is how
images acquire interesting corruption, and mixed-ending
files are flagged on the way in as the disease the filter
exists to cure.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid

STYLES = ("lf", "crlf")


def looks_binary(content: bytes) -> bool:
    return b"\x00" in content


@dataclass
class EndingFilter:
    desk_style: str

    def __post_init__(self) -> None:
        if self.desk_style not in STYLES:
            raise Invalid(
                f"{self.desk_style!r} is not an ending "
                f"style; the menu is {STYLES}"
            )

    def clean(self, path: str, content: bytes) -> tuple[bytes, str]:
        if looks_binary(content):
            return content, (
                f"{path}: binary by sniff test, exempt; "
                "normalizing newlines inside a PNG is how "
                "images acquire interesting corruption"
            )
        crlf_count = content.count(b"\r\n")
        bare_lf = content.count(b"\n") - crlf_count
        note = ""
        if crlf_count and bare_lf:
            note = (
                f"; {path} arrived with mixed endings "
                f"({crlf_count} crlf, {bare_lf} lf), the "
                "disease this filter exists to cure"
            )
        normalized = content.replace(b"\r\n", b"\n")
        redressed, _ = self.smudge(path, normalized)
        recleaned = redressed.replace(b"\r\n", b"\n")
        if recleaned != normalized:
            raise Invalid(
                f"{path}: the filter pair is not an inverse "
                "on this content; a drifting pair turns every "
                "cycle into a phantom diff machine"
            )
        return normalized, (
            f"{path}: cleaned to bare newlines" + note
        )

    def smudge(
        self, path: str, content: bytes
    ) -> tuple[bytes, str]:
        if looks_binary(content):
            return content, f"{path}: binary, exempt"
        if self.desk_style == "lf":
            return content, f"{path}: desk speaks lf already"
        dressed = content.replace(b"\n", b"\r\n")
        return dressed, (
            f"{path}: dressed in crlf for this desk"
        )
