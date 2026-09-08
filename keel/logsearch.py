"""Log search: questions to history in a grammar of five keys.

Scrolling is not searching, and the query language here is
deliberately small enough to memorize in one reading: bare
words match message text, path: matches commits that
actually touched the prefix, seq: takes a number or a
range, merge: takes only or none, and limit: caps the
answer. Touching is computed against the first parent
rather than trusting the message, because commits routinely
describe files they never changed and the tree does not
editorialize. Unknown keys are refused with the full
grammar in the refusal, since a search tool that answers
no results for a typo teaches people the history is
emptier than it is, which is worse than no search at all.
Terms compose with AND and only AND, because a query
language that grows OR before its users asked has started
optimizing for its own cleverness.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.commits import Commit
from keel.errors import Invalid
from keel.repo import Repo

GRAMMAR = (
    "bare words (message), path:prefix, seq:N or "
    "seq:N-M, merge:only or merge:none, limit:N"
)


@dataclass
class Query:
    words: list[str] = field(default_factory=list)
    path_prefixes: list[str] = field(default_factory=list)
    seq_low: int | None = None
    seq_high: int | None = None
    merge_mode: str | None = None
    limit: int | None = None


def parse_query(text: str) -> Query:
    query = Query()
    for term in text.split():
        if ":" not in term:
            query.words.append(term.lower())
            continue
        key, _, value = term.partition(":")
        if not value:
            raise Invalid(
                f"{key}: needs a value; the grammar is "
                f"{GRAMMAR}"
            )
        if key == "path":
            query.path_prefixes.append(value)
        elif key == "seq":
            low, dash, high = value.partition("-")
            try:
                query.seq_low = int(low)
                query.seq_high = (
                    int(high) if dash else query.seq_low
                )
            except ValueError as wrong:
                raise Invalid(
                    f"seq: takes a number or N-M, not "
                    f"{value!r}"
                ) from wrong
        elif key == "merge":
            if value not in ("only", "none"):
                raise Invalid(
                    "merge: takes only or none, not "
                    f"{value!r}"
                )
            if (
                query.merge_mode is not None
                and query.merge_mode != value
            ):
                raise Invalid(
                    "merge:only and merge:none together "
                    "match the empty set; say which"
                )
            query.merge_mode = value
        elif key == "limit":
            try:
                query.limit = int(value)
            except ValueError as wrong:
                raise Invalid(
                    f"limit: takes a number, not {value!r}"
                ) from wrong
            if query.limit < 1:
                raise Invalid(
                    "limit: below one answers nothing "
                    "on purpose; leave it off instead"
                )
        else:
            raise Invalid(
                f"{key}: is not in the grammar; the "
                f"grammar is {GRAMMAR}"
            )
    return query


def _touched(
    repo: Repo, commit: Commit, prefix: str
) -> bool:
    current = repo.files_at(commit.address)
    if not commit.parents:
        return any(
            path.startswith(prefix) for path in current
        )
    parent = repo.files_at(commit.parents[0])
    for path in set(current) | set(parent):
        if not path.startswith(prefix):
            continue
        if current.get(path) != parent.get(path):
            return True
    return False


def _matches(
    repo: Repo, commit: Commit, query: Query
) -> bool:
    lowered = commit.message.lower()
    if any(word not in lowered for word in query.words):
        return False
    if query.merge_mode == "only" and (
        len(commit.parents) <= 1
    ):
        return False
    if query.merge_mode == "none" and (
        len(commit.parents) > 1
    ):
        return False
    if query.seq_low is not None and (
        commit.sequence < query.seq_low
    ):
        return False
    if query.seq_high is not None and (
        commit.sequence > query.seq_high
    ):
        return False
    return all(
        _touched(repo, commit, prefix)
        for prefix in query.path_prefixes
    )


def search(
    repo: Repo, tip: str, text: str
) -> list[Commit]:
    query = parse_query(text)
    found = [
        commit
        for commit in repo.graph.log(tip)
        if _matches(repo, commit, query)
    ]
    if query.limit is not None:
        found = found[: query.limit]
    return found


def render(repo: Repo, tip: str, text: str) -> str:
    found = search(repo, tip, text)
    if not found:
        return (
            f"nothing matched {text!r}; the query was "
            "understood, the history just disagrees"
        )
    lines = [f"{len(found)} commit(s) match {text!r}:"]
    lines.extend(
        f"  {commit.address[:8]} "
        f"{commit.message.splitlines()[0]}"
        for commit in found
    )
    return "\n".join(lines)
