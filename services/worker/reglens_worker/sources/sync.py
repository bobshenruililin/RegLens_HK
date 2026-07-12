"""RC3 source metadata sync and policy-gated acquisition orchestration."""

from __future__ import annotations

import argparse
import hashlib
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from reglens_worker.pg.conn import transaction

from .adapters.base import BaseSourceAdapter, FetchHtml, SourceItem
from .adapters.dchk import DchkAdapter
from .adapters.health import assert_parser_health, check_parser_health
from .adapters.mchk import MchkAdapter
from .http_client import FetchResult, SafeHttpClient
from .policy import (
    Policy,
    assert_enabled,
    assert_live_prerequisites,
    assert_mode_allows_acquire,
    get_policy,
    user_agent_contact,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_FIXTURE_DIR = REPO_ROOT / "fixtures" / "source_html"


class SourceSyncError(RuntimeError):
    """Raised when source sync cannot run safely."""


@dataclass(frozen=True)
class SyncResult:
    """Result summary for one source sync run."""

    run_id: uuid.UUID
    source_id: str
    mode: str
    dry_run: bool
    live: bool
    discovered_count: int
    persisted_count: int
    acquired_count: int
    parser_health: dict[str, Any]
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable result."""
        return {
            "run_id": str(self.run_id),
            "source_id": self.source_id,
            "mode": self.mode,
            "dry_run": self.dry_run,
            "live": self.live,
            "discovered_count": self.discovered_count,
            "persisted_count": self.persisted_count,
            "acquired_count": self.acquired_count,
            "parser_health": self.parser_health,
            "errors": list(self.errors),
        }


def get_adapter(source_id: str) -> BaseSourceAdapter:
    """Return the source adapter for a policy source_id."""
    adapters: dict[str, BaseSourceAdapter] = {
        MchkAdapter.source_id: MchkAdapter(),
        DchkAdapter.source_id: DchkAdapter(),
    }
    try:
        return adapters[source_id]
    except KeyError as exc:
        raise SourceSyncError(f"no source adapter for source_id={source_id!r}") from exc


def sync_source(
    source_id: str,
    *,
    dry_run: bool = True,
    acquire: bool = False,
    live: bool = False,
    fixture_dir: str | Path = DEFAULT_FIXTURE_DIR,
    http_client_factory: Callable[[Policy], SafeHttpClient] | None = None,
    conn: psycopg.Connection | None = None,
    limit: int | None = None,
    max_requests_per_run: int | None = None,
) -> SyncResult:
    """
    Run metadata discovery and optional acquisition for one source.

    Fixture replay is used unless `live=True`. Non-dry-run persistence and document
    acquisition both require policy/live prerequisites. Dry-run live metadata health
    only requires an operator contact User-Agent (no Postgres).
    """
    policy = assert_enabled(get_policy(source_id))
    if acquire:
        policy = assert_mode_allows_acquire(policy)
    if acquire or not dry_run:
        assert_live_prerequisites(policy)
    elif live:
        # Manual/CI live metadata health: network + contact only.
        user_agent_contact(policy)

    if max_requests_per_run is not None:
        if max_requests_per_run < 1:
            raise SourceSyncError("--max-requests must be >= 1")
        policy = dict(policy)
        policy["max_requests_per_run"] = int(max_requests_per_run)

    adapter = get_adapter(source_id)
    mode = _sync_mode(dry_run=dry_run, acquire=acquire)
    run_id = uuid.uuid4()
    client_factory = http_client_factory or _default_http_client_factory
    live_client = client_factory(policy) if live else None
    index_url, index_html, fetch_result = _load_index(
        policy,
        adapter,
        live=live,
        fixture_dir=Path(fixture_dir),
        client=live_client,
    )
    fetch_html: FetchHtml
    if live:
        assert live_client is not None

        def _live_fetch_html(url: str) -> str:
            result = live_client.fetch(url, purpose="index")
            return result.temp_path.read_text(encoding="utf-8")

        fetch_html = _live_fetch_html
    else:
        fetch_html = _fixture_fetcher(adapter, Path(fixture_dir), index_url)
    items = list(adapter.discover(index_html, base_url=index_url, fetch_html=fetch_html))
    if limit is not None:
        if limit < 0:
            raise SourceSyncError("--limit must be >= 0")
        items = items[:limit]
    health = check_parser_health(
        index_html,
        items,
        required_markers=_required_markers(source_id),
    )
    assert_parser_health(health)

    acquired_count = 0
    if acquire:
        client = live_client or client_factory(policy)
        for item in items:
            if not item.document_url:
                continue
            adapter.acquire(item, client)
            acquired_count += 1

    if dry_run:
        return SyncResult(
            run_id=run_id,
            source_id=source_id,
            mode=mode,
            dry_run=True,
            live=live,
            discovered_count=len(items),
            persisted_count=0,
            acquired_count=acquired_count,
            parser_health=health.to_dict(),
        )

    if conn is not None:
        run_id = _persist_run(conn, policy, adapter, mode, live)
        persisted_count = _persist_discovery(
            conn,
            run_id=run_id,
            policy=policy,
            index_url=index_url,
            index_html=index_html,
            items=items,
            health=health.to_dict(),
            fetch_result=fetch_result,
        )
        _finish_run(conn, run_id, "succeeded", len(items), persisted_count, acquired_count)
    else:
        with transaction() as tx:
            run_id = _persist_run(tx, policy, adapter, mode, live)
            persisted_count = _persist_discovery(
                tx,
                run_id=run_id,
                policy=policy,
                index_url=index_url,
                index_html=index_html,
                items=items,
                health=health.to_dict(),
                fetch_result=fetch_result,
            )
            _finish_run(tx, run_id, "succeeded", len(items), persisted_count, acquired_count)

    return SyncResult(
        run_id=run_id,
        source_id=source_id,
        mode=mode,
        dry_run=False,
        live=live,
        discovered_count=len(items),
        persisted_count=persisted_count,
        acquired_count=acquired_count,
        parser_health=health.to_dict(),
    )


def _sync_mode(*, dry_run: bool, acquire: bool) -> str:
    if acquire:
        return "document_acquire"
    if dry_run:
        return "metadata_dry_run"
    return "metadata_sync"


def _load_index(
    policy: Policy,
    adapter: BaseSourceAdapter,
    *,
    live: bool,
    fixture_dir: Path,
    client: SafeHttpClient | None = None,
) -> tuple[str, str, FetchResult | None]:
    index_url = str(policy["official_index_urls"][0])
    if live:
        if client is None:
            raise SourceSyncError("live index fetch requires a shared SafeHttpClient")
        result = client.fetch(index_url, purpose="index")
        return index_url, result.temp_path.read_text(encoding="utf-8"), result

    fixture_path = _fixture_path(adapter, fixture_dir)
    return index_url, fixture_path.read_text(encoding="utf-8"), None


def _default_http_client_factory(policy: Policy) -> SafeHttpClient:
    return SafeHttpClient(policy)


def _fixture_path(adapter: BaseSourceAdapter, fixture_dir: Path) -> Path:
    if adapter.source_id == "mchk_judgments":
        return fixture_dir / "mchk" / "index_root.synthetic.html"
    if adapter.source_id == "dchk_judgments":
        return fixture_dir / "dchk" / "judgments_table.synthetic.html"
    raise SourceSyncError(f"no fixture mapping for {adapter.source_id}")


def _fixture_fetcher(
    adapter: BaseSourceAdapter,
    fixture_dir: Path,
    index_url: str,
) -> Callable[[str], str]:
    def fetch(url: str) -> str:
        _ = index_url
        parsed = urlparse(url)
        name = Path(parsed.path).name
        if adapter.source_id == "mchk_judgments" and name == "year_page.synthetic.html":
            return (fixture_dir / "mchk" / "year_page.synthetic.html").read_text(encoding="utf-8")
        raise SourceSyncError(f"offline fixture not found for URL {url}")

    return fetch


def _required_markers(source_id: str) -> tuple[str, ...]:
    # Health passes when at least one marker is present (synthetic or live layout).
    if source_id == "mchk_judgments":
        return (
            "#judgment-years",
            "table#judgments",
            'a[href*="year="]',
            'a[href*="_judgments"]',
        )
    if source_id == "dchk_judgments":
        return ("table#judgments",)
    return ()


def _persist_run(
    conn: psycopg.Connection,
    policy: Policy,
    adapter: BaseSourceAdapter,
    mode: str,
    live: bool,
) -> uuid.UUID:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO source_sync_runs (
                source_id, adapter_id, adapter_version, mode, status, dry_run,
                live, policy_snapshot, request_budget
            ) VALUES (
                %s, %s, %s, %s, 'running', FALSE,
                %s, %s, %s
            )
            RETURNING id
            """,
            (
                policy["source_id"],
                adapter.adapter_id,
                adapter.adapter_version,
                mode,
                live,
                Jsonb(policy),
                int(policy["max_requests_per_run"]),
            ),
        )
        row = cur.fetchone()
    if row is None:
        raise SourceSyncError("source_sync_runs insert returned no row")
    return row["id"]


def _persist_discovery(
    conn: psycopg.Connection,
    *,
    run_id: uuid.UUID,
    policy: Policy,
    index_url: str,
    index_html: str,
    items: Sequence[SourceItem],
    health: dict[str, Any],
    fetch_result: FetchResult | None,
) -> int:
    snapshot_id = _insert_snapshot(
        conn,
        run_id=run_id,
        policy=policy,
        index_url=index_url,
        index_html=index_html,
        item_count=len(items),
        health=health,
        fetch_result=fetch_result,
    )
    _upsert_alias(conn, policy["source_id"], None, index_url, "index")
    persisted = 0
    for item in items:
        item_id = _upsert_item(conn, item, run_id=run_id, snapshot_id=snapshot_id)
        if item.source_url:
            _upsert_alias(conn, item.source_id, item_id, item.source_url, "detail")
        if item.document_url:
            _upsert_alias(conn, item.source_id, item_id, item.document_url, "document")
        persisted += 1
    return persisted


def _insert_snapshot(
    conn: psycopg.Connection,
    *,
    run_id: uuid.UUID,
    policy: Policy,
    index_url: str,
    index_html: str,
    item_count: int,
    health: dict[str, Any],
    fetch_result: FetchResult | None,
) -> uuid.UUID:
    content = index_html.encode("utf-8")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO source_index_snapshots (
                run_id, source_id, index_url, snapshot_status, http_status,
                content_sha256, byte_size, item_count, parser_health_json,
                raw_fixture_path, storage_path
            ) VALUES (
                %s, %s, %s, 'parsed', %s,
                %s, %s, %s, %s,
                %s, %s
            )
            RETURNING id
            """,
            (
                run_id,
                policy["source_id"],
                index_url,
                fetch_result.status_code if fetch_result else None,
                hashlib.sha256(content).hexdigest(),
                len(content),
                item_count,
                Jsonb(health),
                None if fetch_result else "fixtures/source_html",
                str(fetch_result.temp_path) if fetch_result else None,
            ),
        )
        row = cur.fetchone()
    if row is None:
        raise SourceSyncError("source_index_snapshots insert returned no row")
    return row["id"]


def _upsert_item(
    conn: psycopg.Connection,
    item: SourceItem,
    *,
    run_id: uuid.UUID,
    snapshot_id: uuid.UUID,
) -> uuid.UUID:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO discovered_source_items (
                source_id, source_item_key, status, title, source_url,
                document_url, case_refs, inquiry_dates, judgment_date,
                published_date, metadata_json, caveats_json, last_sync_run_id,
                last_snapshot_id
            ) VALUES (
                %s, %s, 'seen', %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s
            )
            ON CONFLICT (source_id, source_item_key) DO UPDATE SET
                status = 'seen',
                title = EXCLUDED.title,
                source_url = EXCLUDED.source_url,
                document_url = EXCLUDED.document_url,
                case_refs = EXCLUDED.case_refs,
                inquiry_dates = EXCLUDED.inquiry_dates,
                judgment_date = EXCLUDED.judgment_date,
                published_date = EXCLUDED.published_date,
                metadata_json = EXCLUDED.metadata_json,
                caveats_json = EXCLUDED.caveats_json,
                last_sync_run_id = EXCLUDED.last_sync_run_id,
                last_snapshot_id = EXCLUDED.last_snapshot_id,
                missing_since = NULL,
                last_seen_at = now(),
                updated_at = now()
            RETURNING id
            """,
            (
                item.source_id,
                item.source_item_key,
                item.title,
                item.source_url,
                item.document_url,
                Jsonb(list(item.case_refs)),
                Jsonb(list(item.inquiry_dates)),
                item.judgment_date,
                item.published_date,
                Jsonb(dict(item.metadata)),
                Jsonb(list(item.caveats)),
                run_id,
                snapshot_id,
            ),
        )
        row = cur.fetchone()
    if row is None:
        raise SourceSyncError("discovered_source_items upsert returned no row")
    return row["id"]


def _upsert_alias(
    conn: psycopg.Connection,
    source_id: str,
    item_id: uuid.UUID | None,
    url: str,
    url_kind: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO source_url_aliases (
                source_id, discovered_source_item_id, url, url_kind
            ) VALUES (
                %s, %s, %s, %s
            )
            ON CONFLICT (source_id, url) DO UPDATE SET
                discovered_source_item_id = COALESCE(
                    EXCLUDED.discovered_source_item_id,
                    source_url_aliases.discovered_source_item_id
                ),
                url_kind = EXCLUDED.url_kind,
                last_seen_at = now()
            """,
            (source_id, item_id, url, url_kind),
        )


def _finish_run(
    conn: psycopg.Connection,
    run_id: uuid.UUID,
    status: str,
    discovered_count: int,
    persisted_count: int,
    acquired_count: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE source_sync_runs
            SET status = %s,
                items_discovered = %s,
                items_persisted = %s,
                documents_acquired = %s,
                finished_at = now()
            WHERE id = %s
            """,
            (status, discovered_count, persisted_count, acquired_count, run_id),
        )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for source sync."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--fixture-dir", default=str(DEFAULT_FIXTURE_DIR))
    parser.add_argument("--live", action="store_true", help="fetch official index over HTTP")
    parser.add_argument("--acquire", action="store_true", help="policy-gated document acquisition")
    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="persist metadata to PostgreSQL; requires REGLENS_MODE=postgres",
    )
    args = parser.parse_args(argv)

    result = sync_source(
        args.source_id,
        dry_run=not args.no_dry_run,
        acquire=args.acquire,
        live=args.live,
        fixture_dir=args.fixture_dir,
    )
    print(result.to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
