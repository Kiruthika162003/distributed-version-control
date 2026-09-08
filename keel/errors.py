"""The error family: every refusal in this system descends from one name."""

from __future__ import annotations


class KeelError(Exception):
    """Base for everything this version control system refuses to do."""


class Invalid(KeelError):
    """The request contradicts itself or the repository's rules."""


class Missing(KeelError):
    """The object, ref, or path addressed does not exist."""


class Conflict(KeelError):
    """Two histories disagree and a human must pick."""


class Corrupt(KeelError):
    """Bytes do not match their address; the store is compromised."""


class Detached(KeelError):
    """The operation needs a branch and HEAD is not on one."""
