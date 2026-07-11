"""Studio users and sessions (scrypt passwords, hashed session tokens)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row

# OWASP-aligned scrypt parameters for interactive logins.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64
_SALT_BYTES = 16


class AuthError(ValueError):
    """Authentication / session failure."""


def hash_password(password: str) -> str:
    """Return `scrypt$N$r$p$salt_b64$hash_b64`."""
    if not password:
        raise AuthError("password must be non-empty")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(digest).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt_b64}${hash_b64}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored scrypt hash (constant-time compare)."""
    try:
        algo, n_s, r_s, p_s, salt_b64, hash_b64 = stored.split("$", 5)
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    try:
        n = int(n_s)
        r = int(r_s)
        p = int(p_s)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(hash_b64.encode("ascii"))
    except (ValueError, TypeError):
        return False
    actual = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=len(expected),
    )
    return hmac.compare_digest(actual, expected)


def hash_session_token(token: str) -> str:
    """SHA-256 hex digest of a raw session token (what we store)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(
    conn: psycopg.Connection,
    *,
    username: str,
    password: str,
    role: str,
    display_name: str | None = None,
    active: bool = True,
    user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    if role not in {"reviewer", "publisher", "admin"}:
        raise AuthError(f"Invalid role={role!r}")
    password_hash = hash_password(password)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO users (id, username, password_hash, role, active, display_name)
            VALUES (COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s, %s)
            RETURNING id, username, role, active, display_name, created_at, updated_at
            """,
            (user_id, username.strip(), password_hash, role, active, display_name),
        )
        row = cur.fetchone()
        if row is None:
            raise AuthError("create_user returned no row")
        return dict(row)


def verify_user_password(
    conn: psycopg.Connection,
    *,
    username: str,
    password: str,
) -> dict[str, Any] | None:
    """Return the user row (without password_hash) if credentials are valid."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, username, password_hash, role, active, display_name, created_at, updated_at
            FROM users
            WHERE username = %s
            """,
            (username.strip(),),
        )
        row = cur.fetchone()
        if row is None or not row["active"]:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        out = dict(row)
        out.pop("password_hash", None)
        return out


def create_session(
    conn: psycopg.Connection,
    *,
    user_id: uuid.UUID | str,
    ttl_hours: int = 12,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Create a session. Returns `(raw_token, session_row)`.

    Only the SHA-256 of the token is stored.
    """
    token = secrets.token_urlsafe(32)
    token_digest = hash_session_token(token)
    expires_at = datetime.now(UTC) + timedelta(hours=ttl_hours)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO sessions (
                user_id, token_hash, expires_at, user_agent, ip_address, last_seen_at
            ) VALUES (%s, %s, %s, %s, %s, now())
            RETURNING *
            """,
            (user_id, token_digest, expires_at, user_agent, ip_address),
        )
        row = cur.fetchone()
        if row is None:
            raise AuthError("create_session returned no row")
        return token, dict(row)


def revoke_session(
    conn: psycopg.Connection,
    *,
    token: str | None = None,
    token_hash: str | None = None,
    session_id: uuid.UUID | str | None = None,
) -> dict[str, Any] | None:
    """Revoke a session by raw token, token hash, or session id."""
    digest = token_hash
    if token is not None:
        digest = hash_session_token(token)
    with conn.cursor(row_factory=dict_row) as cur:
        if session_id is not None:
            cur.execute(
                """
                UPDATE sessions
                SET revoked_at = now()
                WHERE id = %s AND revoked_at IS NULL
                RETURNING *
                """,
                (session_id,),
            )
        elif digest is not None:
            cur.execute(
                """
                UPDATE sessions
                SET revoked_at = now()
                WHERE token_hash = %s AND revoked_at IS NULL
                RETURNING *
                """,
                (digest,),
            )
        else:
            raise AuthError("token, token_hash, or session_id required")
        row = cur.fetchone()
        return dict(row) if row else None


def lookup_session(
    conn: psycopg.Connection,
    token: str,
) -> dict[str, Any] | None:
    """Return active (non-revoked, non-expired) session + user fields for a raw token."""
    digest = hash_session_token(token)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                s.*,
                u.username,
                u.role,
                u.active AS user_active,
                u.display_name
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = %s
              AND s.revoked_at IS NULL
              AND s.expires_at > now()
              AND u.active = TRUE
            """,
            (digest,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cur.execute(
            "UPDATE sessions SET last_seen_at = now() WHERE id = %s",
            (row["id"],),
        )
        return dict(row)
