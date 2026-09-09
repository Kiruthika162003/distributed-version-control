# Running distributed-version-control

A content addressed version control system, written in Python. This file covers how to build
the project, run its tests, and execute it. Every command below was run from a
clean checkout of this repository before being written down.

## Requirements

Python 3.11 or newer. There are no third party runtime dependencies.

## Setup

Nothing to install. The package has no dependencies, so every command below
runs from the repository root against the source tree as it stands.

## Run the tests

```bash
python -m pytest -q
```

The suite is the primary check. It runs from the repository root with no
arguments and no configuration, and it prints the number of tests it ran. A
non-zero exit status means something is wrong. Read the printed summary rather
than a shell pipeline, because piping the output through another command
replaces the real exit code with that of the last command in the pipe.

## Lint

```bash
python -m ruff check .
```

The lint configuration lives in `pyproject.toml`. It passes with no findings.

## Run the command line tool

```bash
python -m keel.cli --help
```

The subcommands are `witnesses`, `check`, `summary`, `witness`, `demo`, `numbers`, `organs`, `voyages`, `trial`, `colophon`.

For example:

```bash
python -m keel.cli witnesses
```

## Run a worked example

There are 13 runnable examples in `examples/`. Each exposes `run()`, which
returns the lines it would print, and `main()`, which prints them:

```bash
python -c "from examples.archaeologyday import main; main()"
```

The full list is `archaeologyday`, `archivistday`, `collaborationday`, `commissioningday`, `featureweek`, `firstvoyage`, `fleetweek`, `harborday`, and others.

## Layout

- `keel/` the package itself
- `keel/witnesses/` the verification organ, a set of measured claims about the
  package as a whole rather than unit tests of one function
- `tests/` the test suite
- `examples/` runnable end to end scenarios

## Notes

The examples are pinned line by line in the test suite, so an example whose
output drifts fails the build rather than quietly changing. Where a guess about
behaviour was refuted by measurement, the wrong guess is kept in the source
beside the measured value rather than deleted.
