from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

from poe_affix_builder.adapters.json_store import load_json, write_json_atomic
from poe_affix_builder.contracts.manifest_contracts import manifest_to_dict
from poe_affix_builder.contracts.report_contracts import rebuild_report_to_dict
from poe_affix_builder.domain.models import (
    ManifestAffix,
    ManifestBase,
    ManifestDocument,
    ManifestItem,
    ManifestModifierSection,
    ManifestTier,
    RebuildReport,
    RebuildResult,
)
from poe_affix_builder.policies import domain_for_category, spawn_tags_for_slug
from poe_affix_builder.services.diagnostics_service import unresolved_diagnostics_to_dict
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


@dataclass(frozen=True)
class RebuiltModifierSectionResult:
    section: ManifestModifierSection
    unresolved_matches: tuple[dict[str, Any], ...]


def rebuild_modifier_section(
    *,
    slug: str,
    section_name: str,
    rows: list[Any],
    entries_by_family_level: Mapping[tuple[str, int], list[Any]],
    include_domains: set[str],
    include_spawn_tags: set[str],
) -> RebuiltModifierSectionResult:
    affixes_out: list[ManifestAffix] = []
    unresolved_mod_matches: list[dict[str, Any]] = []
    for affix in sorted(
        rows,
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
                include_domains=include_domains,
                include_spawn_tags=include_spawn_tags,
            )
            stats = tuple(_entry_stat_ids(decision.entry)) if decision.entry is not None else ()
            if decision.entry is None:
                unresolved_mod_matches.append(
                    {
                        "section": section_name,
                        "slug": slug,
                        "kind": kind,
                        "family_key": family_key,
                        "level": level,
                        "match_explanation": decision.explanation.reasons,
                    }
                )
            tiers_out.append(ManifestTier(level=level, name=name, text=text, stats=stats))
        affixes_out.append(ManifestAffix(kind=kind, family_key=family_key, template=template, tiers=tuple(tiers_out)))
    return RebuiltModifierSectionResult(
        section=ManifestModifierSection(name=section_name, affixes=tuple(affixes_out)),
        unresolved_matches=tuple(unresolved_mod_matches),
    )


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

    bases = []
    for base in snapshot_item.get("bases") or []:
        if not isinstance(base, Mapping):
            continue
        bases.append(
            ManifestBase(
                name=str(base.get("name") or ""),
                href=str(base.get("href") or ""),
                required_level=base.get("required_level") if isinstance(base.get("required_level"), int) else None,
            )
        )

    snapshot_sections = dict(snapshot_item.get("modifier_sections") or {})
    if "normal" not in snapshot_sections and "affixes" in snapshot_item:
        snapshot_sections["normal"] = snapshot_item.get("affixes") or []

    modifier_sections: list[ManifestModifierSection] = []
    for section_name, rows in sorted(snapshot_sections.items(), key=lambda row: str(row[0])):
        rebuilt_section = rebuild_modifier_section(
            slug=slug,
            section_name=str(section_name),
            rows=list(rows or []),
            entries_by_family_level=entries_by_family_level,
            include_domains=domains_set,
            include_spawn_tags=tags_set,
        )
        modifier_sections.append(rebuilt_section.section)
        unresolved_mod_matches.extend(rebuilt_section.unresolved_matches)

    affixes_out = next((section.affixes for section in modifier_sections if section.name == "normal"), tuple())

    return ManifestItem(
        slug=slug,
        category=category,
        label=label,
        include_domains=include_domains,
        include_spawn_tags=include_spawn_tags,
        bases=tuple(bases),
        modifier_sections=tuple(modifier_sections),
        affixes=affixes_out,
    )


def count_manifest_modifier_sections(items: tuple[ManifestItem, ...] | list[ManifestItem]) -> tuple[int, int]:
    total_affixes = 0
    total_tiers = 0
    for item in items:
        sections = item.modifier_sections or ()
        if sections:
            for section in sections:
                total_affixes += len(section.affixes)
                total_tiers += sum(len(affix.tiers) for affix in section.affixes)
        else:
            total_affixes += len(item.affixes)
            total_tiers += sum(len(affix.tiers) for affix in item.affixes)
    return total_affixes, total_tiers


def rebuild_mapping(
    *,
    mods_json_path: Path,
    snapshot_path: Path,
    out_path: Path,
    report_path: Path,
    diagnostics_path: Path | None = None,
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
    total_affixes, total_tiers = count_manifest_modifier_sections(out_items)
    report = RebuildReport(
        ok=True,
        items=len(out_items),
        affixes=total_affixes,
        tiers=total_tiers,
        unresolved_mod_matches=tuple(
            {
                "slug": row["slug"],
                "kind": row["kind"],
                "family_key": row["family_key"],
                "level": row["level"],
            }
            for row in unresolved_mod_matches
        ),
    )

    write_json_atomic(out_path, manifest_to_dict(document))
    write_json_atomic(report_path, rebuild_report_to_dict(report))
    if diagnostics_path is not None:
        write_json_atomic(diagnostics_path, unresolved_diagnostics_to_dict(unresolved_mod_matches))
    return RebuildResult(items=report.items, affixes=report.affixes, tiers=report.tiers, report=rebuild_report_to_dict(report))
