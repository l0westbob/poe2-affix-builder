from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, Iterable

from poe_affix_builder.adapters.poe2db_html import strip_html

_RANGE_RE = re.compile(r"\(\s*[-+]?\d+(?:\.\d+)?\s*[—–-]\s*[-+]?\d+(?:\.\d+)?\s*\)")
_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?%?")


def normalize_template_from_str(str_html: str) -> str:
    text = strip_html(str_html)
    text = _RANGE_RE.sub("#", text)
    text = _NUM_RE.sub("#", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


def extract_modifier_sections(modsview: Dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    sections: dict[str, list[dict[str, Any]]] = {}
    for key, value in modsview.items():
        if not isinstance(value, list) or not value:
            continue
        rows = [row for row in value if isinstance(row, dict) and "ModGenerationTypeID" in row]
        if not rows:
            continue
        sections[key] = group_affixes(rows)
    return sections
