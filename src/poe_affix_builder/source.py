from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from poe_affix_builder.adapters.json_store import load_json
from poe_affix_builder.domain.models import ModEntry
from poe_affix_builder.normalize import normalize_compare_text, normalize_output_text


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _extract_spawn_tags(mod: dict[str, Any]) -> set[str]:
    tags: set[str] = set()
    for item in mod.get("spawn_weights") or []:
        if isinstance(item, dict) and isinstance(item.get("tag"), str) and item["tag"]:
            tags.add(item["tag"])
    return tags


def _extract_stats(mod: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    stats = mod.get("stats")
    if not isinstance(stats, list):
        return out
    for row in stats:
        if not isinstance(row, dict):
            continue
        stat_id = row.get("id")
        if not isinstance(stat_id, str) or not stat_id:
            continue
        item: dict[str, Any] = {"id": stat_id}
        if "min" in row:
            item["min"] = row.get("min")
        if "max" in row:
            item["max"] = row.get("max")
        out.append(item)
    return out


def _normalize_kind(kind: Any) -> str:
    if isinstance(kind, str):
        return kind
    level = _to_int(kind)
    if level is None:
        return ""
    if level == 1:
        return "prefix"
    if level == 2:
        return "suffix"
    return f"gen{level}"


def load_mod_entries(mods_json_path: Path, *, include_kinds: Iterable[str] | None = None) -> list[ModEntry]:
    raw = load_json(mods_json_path)
    if not isinstance(raw, dict):
        return []

    kinds = set(include_kinds) if include_kinds is not None else None
    entries: list[ModEntry] = []
    for mod_key, mod in raw.items():
        if not isinstance(mod, dict):
            continue
        kind = _normalize_kind(mod.get("generation_type"))
        if not kind or (kinds is not None and kind not in kinds):
            continue
        groups = mod.get("groups") or []
        family_key = groups[0] if isinstance(groups, list) and groups and isinstance(groups[0], str) else ""
        if not family_key:
            continue
        level = _to_int(mod.get("required_level"))
        if level is None:
            continue

        text_out = normalize_output_text(mod.get("text")) or ""
        text_norm = normalize_compare_text(text_out) or ""
        entries.append(
            ModEntry(
                mod_key=str(mod_key),
                kind=kind,
                domain=mod.get("domain") if isinstance(mod.get("domain"), str) else "",
                family_key=family_key,
                required_level=level,
                name=mod.get("name") if isinstance(mod.get("name"), str) else "",
                text=text_out,
                text_norm=text_norm,
                stats=_extract_stats(mod),
                spawn_tags=_extract_spawn_tags(mod),
            )
        )
    return entries
