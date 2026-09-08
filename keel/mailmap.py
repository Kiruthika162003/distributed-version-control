"""Mailmap: one person, many spellings, and the ledger that unifies them.

Authors change employers, fix typos in their own names, and
commit from three machines with three configurations, and
every statistic that groups by author is wrong until the
spellings are unified: the shortlog shows one engineer as
four strangers, none of whom cross the contribution
threshold. The map translates recorded identities to
canonical ones, matching by exact identity first and bare
email second, because the email is the stabler half of most
identity drift, and the mapping composes at read time so
history itself is never rewritten to fix a typo, which would
be trading a cosmetic problem for a cryptographic one. The
audit lists unmapped identities that share an email with a
canonical entry, the near-certain aliases nobody has
confirmed, since the map that maintains itself silently is
the one that merges two real people someday.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid


@dataclass(frozen=True)
class Identity:
    name: str
    email: str

    def render(self) -> str:
        return f"{self.name} <{self.email}>"


@dataclass
class Mailmap:
    exact: dict[Identity, Identity] = field(
        default_factory=dict
    )
    by_email: dict[str, Identity] = field(default_factory=dict)

    def map_exact(
        self, recorded: Identity, canonical: Identity
    ) -> str:
        if recorded == canonical:
            raise Invalid(
                "mapping an identity to itself is a diary "
                "entry, not a rule"
            )
        self.exact[recorded] = canonical
        return (
            f"{recorded.render()} now reads as "
            f"{canonical.render()}"
        )

    def map_email(
        self, email: str, canonical: Identity
    ) -> str:
        if "@" not in email:
            raise Invalid(f"{email!r} is not an email")
        self.by_email[email.lower()] = canonical
        return (
            f"anything from {email} now reads as "
            f"{canonical.render()}"
        )

    def resolve(self, recorded: Identity) -> Identity:
        if recorded in self.exact:
            return self.exact[recorded]
        by_mail = self.by_email.get(recorded.email.lower())
        if by_mail is not None:
            return by_mail
        return recorded

    def shortlog(
        self, recorded_authors: list[Identity]
    ) -> str:
        counts: dict[Identity, int] = {}
        for author in recorded_authors:
            canonical = self.resolve(author)
            counts[canonical] = counts.get(canonical, 0) + 1
        ranked = sorted(
            counts.items(),
            key=lambda held: (-held[1], held[0].email),
        )
        return "\n".join(
            f"{count:>4}  {identity.render()}"
            for identity, count in ranked
        )

    def audit(
        self, recorded_authors: list[Identity]
    ) -> list[str]:
        canonical_identities = set(
            self.exact.values()
        ) | set(self.by_email.values())
        canonical_emails = {
            identity.email.lower()
            for identity in canonical_identities
        }
        suspects = []
        for author in set(recorded_authors):
            if self.resolve(author) != author:
                continue
            if author in canonical_identities:
                continue
            if author.email.lower() in canonical_emails:
                suspects.append(
                    f"{author.render()} shares an email with "
                    "a canonical entry; a near-certain alias "
                    "nobody has confirmed"
                )
        return sorted(suspects)
