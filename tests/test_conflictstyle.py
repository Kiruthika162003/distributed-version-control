from __future__ import annotations

from keel.conflictstyle import ConflictDresser

BASE = {"app.py": b"shared\ncore", "lib.py": b"stable"}
LEFT = {"app.py": b"LEFT\ncore", "lib.py": b"stable"}
RIGHT = {"app.py": b"RIGHT\ncore", "lib.py": b"stable"}


def dresser(
    paths: tuple[str, ...] = ("app.py",),
) -> ConflictDresser:
    return ConflictDresser(
        base_files=dict(BASE),
        left_files=dict(LEFT),
        right_files=dict(RIGHT),
        conflict_paths=paths,
    )


class TestTheThreeDresses:
    def test_the_editor_style_always_shows_the_base(self):
        pages = dresser().editor_style()
        assert "||||||| base" in pages["app.py"]
        assert "<<<<<<< ours" in pages["app.py"]
        assert "shared" in pages["app.py"]

    def test_the_terse_style_names_paths_not_moods(self):
        terse = dresser().terse_style()
        assert terse.startswith("app.py: 1 collision(s)")
        assert "widest 2 line(s)" in terse

    def test_the_structured_style_parses_without_guessing(self):
        records = dresser().structured_style()
        assert len(records) == 1
        assert records[0]["ours"] == ["LEFT"]
        assert records[0]["theirs"] == ["RIGHT"]
        assert records[0]["base"] == ["shared"]

    def test_the_styles_agree_on_the_count(self):
        dressed = dresser().dress_all()
        assert dressed["agreed_count"] == 1
        assert "app.py" in dressed["editor"]

    def test_the_clean_merge_has_nothing_to_dress(self):
        assert dresser(paths=()).terse_style() == (
            "no conflicts; nothing to dress"
        )
