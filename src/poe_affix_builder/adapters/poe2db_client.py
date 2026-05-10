from __future__ import annotations

import re
import time
from collections import defaultdict
from html.parser import HTMLParser
from typing import Any, Callable, Dict, Iterable
from urllib.parse import urljoin, urlparse

import demjson3
import httpx
from selectolax.parser import HTMLParser as SelectolaxHTMLParser

from poe_affix_builder.domain.models import ItemLink

DEFAULT_INDEX_URL = "https://poe2db.tw/us/Modifiers"
BASE = "https://poe2db.tw"
DEFAULT_HEADERS = {
    "User-Agent": "poe-affix-builder/0.1 (+https://example.invalid)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


class _TextStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def strip_html(html: str) -> str:
    parser = _TextStripper()
    parser.feed(html)
    out = parser.get_text()
    return re.sub(r"\s+", " ", out).strip()


_RANGE_RE = re.compile(r"\(\s*[-+]?\d+(?:\.\d+)?\s*[—–-]\s*[-+]?\d+(?:\.\d+)?\s*\)")
_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?%?")
_MODSVIEW_RE = re.compile(r"new\s+ModsView\(\s*(\{.*?\})\s*\)\s*;", re.DOTALL)


def normalize_template_from_str(str_html: str) -> str:
    text = strip_html(str_html)
    text = _RANGE_RE.sub("#", text)
    text = _NUM_RE.sub("#", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def to_abs_no_fragment(href: str) -> str:
    abs_url = urljoin(BASE, href)
    parsed = urlparse(abs_url)
    return parsed._replace(fragment="").geturl()


def slug_from_url(abs_url: str) -> str:
    parsed = urlparse(abs_url)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return "unknown"
    return parts[-1]


def extract_item_links_from_modifiers_index(html: str) -> list[ItemLink]:
    tree = SelectolaxHTMLParser(html)
    root = tree.root

    cards = root.css("div.card")
    target_body = None
    for card in cards:
        header = card.css_first("h5.card-header")
        if header and (header.text() or "").strip() == "Modifiers":
            target_body = card.css_first("div.card-body")
            break

    if not target_body:
        raise RuntimeError('Could not find "Modifiers" card on /us/Modifiers')

    blocks = target_body.css("div.itemList")
    if not blocks:
        raise RuntimeError("Could not find any div.itemList in Modifiers card")

    out: list[ItemLink] = []
    for block in blocks[1:]:
        disabled = block.css_first("span.disabled")
        category = (disabled.text() or "").strip() if disabled else "Uncategorized"
        for node in block.css("a[href]"):
            href = (node.attributes.get("href") or "").strip()
            if not href:
                continue
            abs_url = to_abs_no_fragment(href)
            out.append(
                ItemLink(
                    category=category or "Uncategorized",
                    label=(node.text() or "").strip() or slug_from_url(abs_url),
                    href=abs_url,
                    slug=slug_from_url(abs_url),
                )
            )

    deduped: list[ItemLink] = []
    seen: set[str] = set()
    for row in out:
        if row.href not in seen:
            seen.add(row.href)
            deduped.append(row)
    return deduped


def extract_modsview(html: str) -> Dict[str, Any]:
    match = _MODSVIEW_RE.search(html)
    if not match:
        raise RuntimeError("Could not find 'new ModsView({...})' payload in HTML")

    decoded = demjson3.decode(match.group(1))
    if not isinstance(decoded, dict):
        raise RuntimeError("Parsed ModsView payload is not an object")
    return decoded


def is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526, 527, 530}


def fetch_html_with_client(
    client: httpx.Client,
    url: str,
    *,
    max_attempts: int = 5,
    backoff_s: float = 1.0,
    emit: Callable[[str], None] | None = None,
) -> str:
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.get(url)
        except (httpx.TimeoutException, httpx.TransportError) as err:
            last_err = err
            if attempt >= max_attempts:
                break
            wait_s = backoff_s * (2 ** (attempt - 1))
            if emit is not None:
                emit(
                    f"[poe2db] retry {attempt}/{max_attempts - 1} after transport error for {url}: {err} "
                    f"(sleep {wait_s:.1f}s)"
                )
            time.sleep(wait_s)
            continue

        if resp.status_code >= 400:
            err = httpx.HTTPStatusError(
                f"HTTP {resp.status_code} for url {url}",
                request=resp.request,
                response=resp,
            )
            last_err = err
            if is_retryable_status(resp.status_code) and attempt < max_attempts:
                wait_s = backoff_s * (2 ** (attempt - 1))
                if emit is not None:
                    emit(
                        f"[poe2db] retry {attempt}/{max_attempts - 1} after HTTP {resp.status_code} for {url} "
                        f"(sleep {wait_s:.1f}s)"
                    )
                time.sleep(wait_s)
                continue
            resp.raise_for_status()

        return resp.text

    if last_err is not None:
        raise RuntimeError(f"Failed fetching {url} after {max_attempts} attempts: {last_err}") from last_err
    raise RuntimeError(f"Failed fetching {url} after {max_attempts} attempts")


def fetch_html(
    url: str,
    *,
    timeout_s: float = 30.0,
    max_attempts: int = 5,
    backoff_s: float = 1.0,
    emit: Callable[[str], None] | None = None,
) -> str:
    with httpx.Client(follow_redirects=True, timeout=timeout_s, headers=DEFAULT_HEADERS) as client:
        return fetch_html_with_client(client, url, max_attempts=max_attempts, backoff_s=backoff_s, emit=emit)


def _to_int(value: Any) -> int | None:
    try:
        return int(str(value))
    except Exception:
        return None


def kind_from_generation_type(value: Any) -> str:
    level = _to_int(value)
    if level is None:
        return ""
    if level == 1:
        return "prefix"
    if level == 2:
        return "suffix"
    return f"gen{level}"


def family_key(value: Any) -> str:
    if isinstance(value, list) and value:
        return "|".join(str(v) for v in value)
    if value is None:
        return ""
    return str(value)


def group_affixes(normal_rows: Iterable[Dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: Dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in normal_rows:
        kind = kind_from_generation_type(row.get("ModGenerationTypeID"))
        if not kind:
            continue
        group = family_key(row.get("ModFamilyList")) or "unknown"
        str_html = row.get("str") if isinstance(row.get("str"), str) else ""
        template = normalize_template_from_str(str_html) if str_html else ""
        if not template:
            template = str(row.get("Name") or "unknown")
        level = _to_int(row.get("Level"))
        if level is None:
            continue
        grouped[(kind, group, template)].append(
            {
                "level": level,
                "name": str(row.get("Name") or ""),
                "text": strip_html(str_html) if str_html else "",
                "drop_chance": _to_int(row.get("DropChance")),
            }
        )

    affixes = []
    for key in sorted(grouped):
        kind, group, template = key
        tiers = sorted(grouped[key], key=lambda t: (int(t.get("level") or 0), str(t.get("name") or ""), str(t.get("text") or "")))
        affixes.append({"kind": kind, "family_key": group, "template": template, "tiers": tiers})
    return affixes
