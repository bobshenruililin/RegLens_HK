# ADR 0012 — Studio auth role model

## Status

Accepted (MVP-RC2)

## Context

RC1 Studio used a single shared HMAC password suitable for local demos, not for
separating review vs publication duties or auditing actors.

## Decision

Postgres-backed users with roles:

| Role | Capabilities |
|------|----------------|
| `reviewer` | Review queue: accept / edit / reject |
| `publisher` | Draft, validate, approve publication releases |
| `admin` | User administration + reviewer + publisher |

Passwords stored as scrypt hashes; session tokens stored as SHA-256 digests only.
Production Studio remains fail-closed on missing session secrets where the Next
app enforces them.

Observatory stays unauthenticated and must not import Studio session cookies.

## Consequences

- Audit events can attribute `actor_user_id`.
- Demo bootstrap may create a local admin (labelled local-only password).
- Role checks belong in Studio API / server actions — not in the public site.
