from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any, Dict
from urllib.parse import urljoin, urlparse

import demjson3
from selectolax.parser import HTMLParser as SelectolaxHTMLParser

from poe_affix_builder.domain.models import ItemLink

BASE = "https://poe2db.tw"
_MODSVIEW_RE = re.compile(r"new\s+ModsView\(\s*(\{.*?\})\s*\)\s*;", re.DOTALL)
_REQUIRES_LEVEL_RE = re.compile(r"Requires:\s*Level\s+(\d+)")


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


def _to_int(value: Any) -> int | None:
    try:
        return int(str(value))
    except Exception:
        return None


def extract_item_bases_from_page(html: str) -> list[dict[str, Any]]:
    tree = SelectolaxHTMLParser(html)
    root = tree.root

    item_tab = None
    for pane in root.css("div.tab-content > div.tab-pane"):
        pane_id = (pane.attributes.get("id") or "").strip()
        if pane_id.endswith("Item"):
            item_tab = pane
            break

    if item_tab is None:
        return []

    bases: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for anchor in item_tab.css("div.flex-grow-1 a.whiteitem[href]"):
        name = (anchor.text() or "").strip()
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        href = (anchor.attributes.get("href") or "").strip()
        required_level = None
        parent = anchor.parent
        if parent is not None:
            requirements = parent.css_first("div.requirements")
            if requirements is not None:
                match = _REQUIRES_LEVEL_RE.search(requirements.text(separator=" ", strip=True))
                if match:
                    required_level = _to_int(match.group(1))

        bases.append(
            {
                "name": name,
                "href": to_abs_no_fragment(href) if href else "",
                "required_level": required_level,
            }
        )

    return bases
