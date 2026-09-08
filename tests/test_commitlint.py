from __future__ import annotations

from keel.commitlint import grade, lint_message

GOOD = (
    "Refuse retagging because releases hold still\n"
    "\n"
    "A tag that moves makes shipped-v2 a statement about a\n"
    "moment instead of about bytes."
)


class TestTheRules:
    def test_the_good_message_is_clean(self):
        assert lint_message(GOOD) == []
        assert "2am reader thanks you" in grade(GOOD)

    def test_findings_accumulate_for_one_round_trip(self):
        bad = "update " + "x" * 60 + ".\nbody right here"
        findings = lint_message(bad)
        rules = {finding.rule for finding in findings}
        assert "subject-length" in rules
        assert "subject-period" in rules
        assert "subject-noise" in rules
        assert "blank-before-body" in rules

    def test_the_empty_message_short_circuits(self):
        findings = lint_message("")
        assert len(findings) == 1
        assert findings[0].rule == "subject-exists"

    def test_noise_openers_name_the_2am_reader(self):
        findings = lint_message("wip more parser work")
        assert any(
            "2am reader must skip" in finding.complaint
            for finding in findings
        )

    def test_long_body_lines_are_wrapped_where_terminals_do(self):
        message = GOOD + "\n" + "y" * 80
        findings = lint_message(message)
        assert any(
            finding.rule == "body-wrap"
            for finding in findings
        )


class TestGrading:
    def test_the_grade_explains_its_own_restraint(self):
        report = grade("wip")
        assert "graded, not blocked" in report
        assert "not fewer commits" in report

    def test_each_finding_carries_rule_and_fix(self):
        report = grade("update everything.")
        assert "subject-period:" in report
        assert "titles, not sentences" in report
