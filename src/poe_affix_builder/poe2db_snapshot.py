from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx

from poe_affix_builder.adapters.json_store import write_json_atomic
from poe_affix_builder.adapters.poe2db_html import (
    extract_item_bases_from_page,
    extract_item_links_from_modifiers_index,
    extract_modsview,
)
from poe_affix_builder.adapters.poe2db_http import (
    DEFAULT_HEADERS,
    DEFAULT_INDEX_URL,
    fetch_html,
    fetch_html_with_client,
)
from poe_affix_builder.adapters.poe2db_modifiers import (
    extract_modifier_sections,
    group_affixes,
)

Emitter = Callable[[str], None]


def _default_emit(message: str) -> None:
    print(message, flush=True)


def build_snapshot(
    *,
    fetcher: Callable[[str], str] = fetch_html,
    index_url: str = DEFAULT_INDEX_URL,
    emit: Emitter | None = _default_emit,
) -> dict[str, Any]:
    if fetcher is fetch_html:
        with httpx.Client(follow_redirects=True, timeout=30.0, headers=DEFAULT_HEADERS) as client:
            return _build_snapshot_inner(
                fetcher=lambda url: fetch_html_with_client(client, url, max_attempts=5, backoff_s=1.0, emit=emit),
                index_url=index_url,
                emit=emit,
            )
    return _build_snapshot_inner(fetcher=fetcher, index_url=index_url, emit=emit)


def _emit(emit: Emitter | None, message: str) -> None:
    if emit is not None:
        emit(message)


def _build_snapshot_inner(*, fetcher: Callable[[str], str], index_url: str, emit: Emitter | None) -> dict[str, Any]:
    _emit(emit, f"[poe2db] fetching index {index_url}")
    index_html = fetcher(index_url)
    links = extract_item_links_from_modifiers_index(index_html)
    _emit(emit, f"[poe2db] discovered {len(links)} item pages")

    items: list[dict[str, Any]] = []
    for idx, link in enumerate(links, start=1):
        _emit(emit, f"[poe2db] [{idx}/{len(links)}] fetching {link.slug}")
        page_html = fetcher(link.href)
        modsview = extract_modsview(page_html)
        normal = modsview.get("normal")
        if not isinstance(normal, list):
            raise RuntimeError(f"modsview for {link.slug} has no 'normal' list")
        modifier_sections = extract_modifier_sections(modsview)
        item = {
            "slug": link.slug,
            "category": link.category,
            "label": link.label,
            "href": link.href,
            "bases": extract_item_bases_from_page(page_html),
            "modifier_sections": modifier_sections,
        }
        items.append(item)
        normal_affixes = modifier_sections.get("normal") or group_affixes(row for row in normal if isinstance(row, dict))
        tiers = sum(len(affix.get("tiers") or []) for affix in normal_affixes)
        _emit(emit, f"[poe2db] [{idx}/{len(links)}] done {link.slug}: {len(normal_affixes)} affixes, {tiers} tiers")

    items.sort(key=lambda item: str(item.get("slug") or ""))
    return {
        "version": 1,
        "source": index_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }


def refresh_snapshot(
    *,
    snapshot_path: Path,
    report_path: Path,
    index_url: str = DEFAULT_INDEX_URL,
    fetcher: Callable[[str], str] = fetch_html,
    emit: Emitter | None = _default_emit,
) -> dict[str, Any]:
    started = time.time()
    snapshot = build_snapshot(fetcher=fetcher, index_url=index_url, emit=emit)
    stable_json = json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8")
    snapshot_sha256 = hashlib.sha256(stable_json).hexdigest()

    item_count = len(snapshot.get("items") or [])
    affix_count = 0
    tier_count = 0
    for item in snapshot.get("items") or []:
        if not isinstance(item, dict):
            continue
        modifier_sections = item.get("modifier_sections") or {}
        affixes = modifier_sections.get("normal") or item.get("affixes") or []
        affix_count += len(affixes)
        for affix in affixes:
            if isinstance(affix, dict):
                tier_count += len(affix.get("tiers") or [])

    report = {
        "ok": True,
        "source": index_url,
        "started_at_utc": datetime.fromtimestamp(started, timezone.utc).isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started, 3),
        "items_fetched": item_count,
        "affixes_fetched": affix_count,
        "tiers_fetched": tier_count,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_path": str(snapshot_path),
    }

    write_json_atomic(snapshot_path, snapshot)
    write_json_atomic(report_path, report)
    return report


__all__ = ["DEFAULT_INDEX_URL", "build_snapshot", "extract_item_links_from_modifiers_index", "extract_modsview", "fetch_html", "refresh_snapshot"]
