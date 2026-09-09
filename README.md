# keel

A distributed version control system built as a library, in Python, with no
dependencies beyond the standard library. Content-addressed storage, a commit
DAG ordered by acceptance rather than wall clocks, three-way merge with honest
conflicts, rename detection with its confidence shown, transfer negotiation,
packfile deltas, and roughly a hundred and twenty small modules that each open
with a sentence about what they refuse to do.

## What it is

keel models the whole life of a repository in memory. Snapshots go in as plain
path-to-bytes maps and come out the same way. Everything above the object
store is built from that: branches, tags, the reflog, stash, rebase, cherry
picks, bisect, blame, shallow clones, bundles, mirrors, merge queues, release
channels, and the governance layer that decides what may land where.

The design habit throughout is stated in the module docstrings and enforced in
the tests:

- Refusals explain themselves. An error names what went wrong and what to do
  about it, because a refusal without a reason gets worked around.
- Guesses are corrected by measurement and kept. When a docstring predicted
  one number and the code measured another, the wrong guess stays recorded
  beside the truth.
- Receipts for everything loud. Force pushes, overrides, steals, and
  reclamations land in journals in capitals, because a quiet exception is
  indistinguishable from the rule not working.

## The shape of the code

- `keel/` holds the organs. Storage first (objects, trees, commits, refs,
  repo), then the working tools (diff, merge, rebase, stash, bisect, blame),
  then collaboration (remotes, push, pull, transfer, bundles, mirrors), then
  governance (gatekeeper, customs, departures, harbormaster, freeze, locks,
  budgets, quorum), then the reading instruments (health report, night watch,
  crow's nest, coupling, code age, lifespans, museum, colophon).
- `keel/witnesses/` holds eighteen measured claims. Each witness runs a drill,
  records its numbers, and holds only if the measurement agrees. Several kept
  their refuted first guesses on purpose.
- `examples/` holds thirteen voyages, each a day someone has actually had:
  a feature week, a hotfix flow, a collaboration day, a policy day, a harbor
  day, a fleet week, a commissioning day, and the rest.
- `tests/` holds 1,171 tests, all passing.

## Running it

There is no install step. From the repository root:

```
python -m pytest tests/ -q
python -m keel.cli summary
python -m keel.cli trial
python -m keel.cli organs
python -m keel.cli voyages
python -m keel.cli demo firstvoyage
python -m keel.cli colophon
```

The `trial` verb runs one honest maneuver through each major system. The
`colophon` verb prints the closing page with every number computed at the
moment of printing.

## The numbers

Just over thirty thousand strict lines of Python, counting only lines of code
and excluding docstrings, comments, and blanks. About one hundred and twenty
modules, eighteen witnesses, thirteen examples, ten CLI verbs, and one rule
that never bent: every commit in this history was made with the full test
suite passing.
