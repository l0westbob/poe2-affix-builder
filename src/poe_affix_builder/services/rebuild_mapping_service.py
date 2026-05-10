from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from poe_affix_builder.adapters.json_store import load_json, write_json_atomic
from poe_affix_builder.contracts.manifest_contracts import manifest_to_dict
from poe_affix_builder.contracts.report_contracts import rebuild_report_to_dict
from poe_affix_builder.domain.models import ManifestAffix, ManifestDocument, ManifestItem, ManifestTier, RebuildReport, RebuildResult
from poe_affix_builder.policies import domain_for_category, spawn_tags_for_slug
from poe_affix_builder.services.matching_service import index_entries_by_family_level, select_rebuild_candidate
from poe_affix_builder.source import load_mod_entries


def _normalize_snapshot(snapshot: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in snapshot.get("items") or []:
        if isinstance(item, dict):
            slug = item.get("slug")
            if isinstance(slug, str) and slug:
                out[slug] = dict(item)
    return out


def _entry_stat_ids(entry) -> list[str]:
    out: list[str] = []
    for row in entry.stats:
        stat_id = row.get("id")
        if isinstance(stat_id, str) and stat_id:
            out.append(stat_id)
    return out


def _build_item_from_snapshot(
    *,
    snapshot_item: Mapping[str, Any],
    entries_by_family_level: Mapping[tuple[str, int], list[Any]],
    unresolved_mod_matches: list[dict[str, Any]],
) -> ManifestItem:
    slug = str(snapshot_item.get("slug") or "")
    category = str(snapshot_item.get("category") or "")
    label = str(snapshot_item.get("label") or slug)
    include_domains = (domain_for_category(category),)
    include_spawn_tags = tuple(spawn_tags_for_slug(slug))
    domains_set = set(include_domains)
    tags_set = set(include_spawn_tags)

    affixes_out: list[ManifestAffix] = []
    for affix in sorted(
        snapshot_item.get("affixes") or [],
        key=lambda row: (str((row or {}).get("kind") or ""), str((row or {}).get("family_key") or ""), str((row or {}).get("template") or "")),
    ):
        if not isinstance(affix, dict):
            continue
        tiers_out: list[ManifestTier] = []
        kind = str(affix.get("kind") or "")
        family_key = str(affix.get("family_key") or "")
        template = str(affix.get("template") or "")
        for tier in sorted(
            affix.get("tiers") or [],
            key=lambda row: (int((row or {}).get("level") or 0), str((row or {}).get("name") or ""), str((row or {}).get("text") or "")),
        ):
            if not isinstance(tier, dict):
                continue
            level = tier.get("level")
            if not isinstance(level, int):
                continue
            name = tier.get("name") if isinstance(tier.get("name"), str) else ""
            text = tier.get("text") if isinstance(tier.get("text"), str) else ""
            candidates = entries_by_family_level.get((family_key, level), [])
            decision = select_rebuild_candidate(
                candidates,
                kind=kind,
                text=text,
                name=name,
                include_domains=domains_set,
                include_spawn_tags=tags_set,
            )
            stats = tuple(_entry_stat_ids(decision.entry)) if decision.entry is not None else ()
            if decision.entry is None:
                unresolved_mod_matches.append({"slug": slug, "kind": kind, "family_key": family_key, "level": level})
            tiers_out.append(ManifestTier(level=level, name=name, text=text, stats=stats))
        affixes_out.append(ManifestAffix(kind=kind, family_key=family_key, template=template, tiers=tuple(tiers_out)))

    return ManifestItem(
        slug=slug,
        category=category,
        label=label,
        include_domains=include_domains,
        include_spawn_tags=include_spawn_tags,
        affixes=tuple(affixes_out),
    )


def rebuild_mapping(
    *,
    mods_json_path: Path,
    snapshot_path: Path,
    out_path: Path,
    report_path: Path,
) -> RebuildResult:
    snapshot = load_json(snapshot_path)
    entries = load_mod_entries(mods_json_path)
    entries_by_family_level = index_entries_by_family_level(entries)
    snapshot_by_slug = _normalize_snapshot(snapshot)
    unresolved_mod_matches: list[dict[str, Any]] = []

    out_items = []
    for _, snapshot_item in sorted(snapshot_by_slug.items(), key=lambda row: row[0]):
        out_items.append(
            _build_item_from_snapshot(
                snapshot_item=snapshot_item,
                entries_by_family_level=entries_by_family_level,
                unresolved_mod_matches=unresolved_mod_matches,
            )
        )

    document = ManifestDocument(version=1, items=tuple(out_items))
    total_affixes = sum(len(item.affixes) for item in out_items)
    total_tiers = sum(len(affix.tiers) for item in out_items for affix in item.affixes)
    report = RebuildReport(
        ok=True,
        items=len(out_items),
        affixes=total_affixes,
        tiers=total_tiers,
        unresolved_mod_matches=tuple(dict(row) for row in unresolved_mod_matches),
    )

    write_json_atomic(out_path, manifest_to_dict(document))
    write_json_atomic(report_path, rebuild_report_to_dict(report))
    return RebuildResult(items=report.items, affixes=report.affixes, tiers=report.tiers, report=rebuild_report_to_dict(report))
