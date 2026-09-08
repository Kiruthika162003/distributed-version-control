"""Dot export: the history graph drawn for eyes instead of walks.

Some history questions are shape questions, where did the
long-lived branch diverge, how tangled were the merges of
March, and shape questions want a picture. The exporter
renders the commit DAG as dot source: nodes labeled with
short address and first message line, edges from child to
parent because history points backward, branch tips and tags
decorated so the names people navigate by appear on the
picture they navigate with. The export is bounded by a node
budget and truncates from the oldest end with a marker node
saying how much was cut, because an unbounded render of a
decade of history produces a picture that crashes the viewer
and answers nothing, and the marker keeps the truncation
from masquerading as the root.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.repo import Repo
from keel.tags import TagStore


def _escape(text: str) -> str:
    return text.replace('"', "'")


def export_dot(
    repo: Repo,
    tip: str,
    tags: TagStore | None = None,
    node_budget: int = 50,
) -> str:
    if node_budget < 2:
        raise Invalid(
            "a budget under two nodes draws a dot, not a graph"
        )
    ordered = sorted(
        repo.graph.ancestors(tip),
        key=lambda a: -repo.graph.get(a).sequence,
    )
    shown = ordered[:node_budget]
    cut = len(ordered) - len(shown)
    shown_set = set(shown)
    lines = ["digraph history {", "  rankdir=BT;"]
    tag_names: dict[str, list[str]] = {}
    if tags is not None:
        for name in tags.tags:
            tag_names.setdefault(
                tags.resolve(name), []
            ).append(name)
    tip_names: dict[str, list[str]] = {}
    for branch, branch_tip in repo.refs.branches.items():
        tip_names.setdefault(branch_tip, []).append(branch)
    for address in shown:
        commit = repo.graph.get(address)
        subject = _escape(
            commit.message.splitlines()[0][:40]
        )
        decorations = []
        decorations.extend(
            f"[{b}]" for b in tip_names.get(address, [])
        )
        decorations.extend(
            f"<{t}>"
            for t in tag_names.get(address, [])
        )
        label = f"{address[:8]} {subject}"
        if decorations:
            label += " " + " ".join(decorations)
        lines.append(
            f'  "{address[:8]}" [label="{label}"];'
        )
        for parent in commit.parents:
            if parent in shown_set:
                lines.append(
                    f'  "{address[:8]}" -> "{parent[:8]}";'
                )
            else:
                lines.append(
                    f'  "{address[:8]}" -> "beyond";'
                )
    if cut:
        lines.append(
            f'  "beyond" [label="{cut} older commit(s) '
            'cut by the budget; not the root"];'
        )
    lines.append("}")
    return "\n".join(lines)
